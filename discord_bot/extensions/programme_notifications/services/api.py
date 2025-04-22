"""An API client to query session information.

Detailed session information is fetched from two different sources, the
Pretalx API and the EuroPython API. This API-client provides an
abstraction layer in which the caller does not have to care about the
actual endpoint that gets polled.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import pathlib
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import aiohttp
import arrow
import attrs
import cattrs
import yarl
from attrs import validators

from discord_bot.extensions.programme_notifications import configuration, exceptions
from discord_bot.extensions.programme_notifications.domain import discord, europython

if TYPE_CHECKING:
    from collections.abc import Iterable

_DEFAULT_SCHEDULE_CACHE_PATH: pathlib.Path = pathlib.Path(__file__).resolve().parent / "_cached" / "schedule.json"
_logger = logging.getLogger(f"bot.{__name__}")
_T = TypeVar("_T")


class IApiClient(Protocol):
    """Protocol for an API client."""

    async def fetch_schedule(self) -> ScheduleResponse:
        """Fetch the latest schedule."""

    async def fetch_session_details(self, session_id: str) -> tuple[yarl.URL, str]:
        """Fetch detailed session information."""

    async def execute_webhook(self, message: discord.WebhookMessage, *, webhook: str) -> None:
        """Execute a Discord webhook."""


@attrs.define(slots=False)
class ApiClient:
    """A client that wraps around external APIs."""

    session: aiohttp.ClientSession = attrs.field(kw_only=True)
    config: configuration.NotifierConfiguration = attrs.field(kw_only=True)
    _schedule_cache_path: pathlib.Path = attrs.field(
        kw_only=True,
        default=_DEFAULT_SCHEDULE_CACHE_PATH,
        validator=validators.instance_of(pathlib.Path),
    )

    @_schedule_cache_path.validator
    def _cache_path_exists_validator(self, attribute: str, value: pathlib.Path) -> None:
        """Validate that the schedule cache path exists."""
        del attribute  # unused
        if not value.exists():
            msg = "The path '%s' does not exist!"
            raise ValueError(msg)

    async def fetch_schedule(self) -> ScheduleResponse:
        """Fetch the schedule from the Pretalx API.

        :return: A `europython.Schedule` instance,
        """
        url = self.config.pretalx_schedule_url
        try:
            response_content = await self._fetch_schedule(url)
        except Exception:
            _logger.exception("Fetching the schedule failed, returned cached version.")
            response_content = self._cached_schedule_response_content
            from_cache = True
        else:
            _logger.info("Fetched schedule from Pretalx, not using cache.")
            from_cache = False

        raw_schedule = json.loads(response_content)
        schedule = europython.Schedule(
            sessions=self._convert(raw_schedule["slots"], europython.Session),
            breaks=self._convert(raw_schedule["breaks"], europython.Break),
            version=raw_schedule["version"],
            schedule_hash=hashlib.sha1(response_content).hexdigest(),  # noqa: S324
        )
        return ScheduleResponse(schedule=schedule, from_cache=from_cache)

    async def _fetch_schedule(self, url: str) -> bytes:
        """Fetch the schedule from Pretalx."""
        _logger.info("Making call to Pretalx API.")
        async with self.session.get(url=url, raise_for_status=True) as response:
            return await response.read()

    @functools.cached_property
    def _cached_schedule_response_content(self) -> bytes:
        """Get and cache the cached schedule response content."""
        return self._schedule_cache_path.read_bytes()

    def _convert(self, raw_instances: Iterable[dict[str, Any]], target_cls: type[_T]) -> list[_T]:
        """Convert the iterable of instance values to a class instance.

        If structuring the raw instance fails, it is ignored. This means
        that no notifications will be sent for that session, but also
        ensures that an unexpected payload does not break the notifier.

        :param raw_instances: The raw instances to convert
        :param target_cls: The target class
        :return: A list of structured class instances
        """
        structured_instances = []
        for raw_instance in raw_instances:
            try:
                structured_instance = self._session_converter.structure(raw_instance, target_cls)
            except cattrs.BaseValidationError:
                _logger.exception("Failed to convert %r to %s", raw_instance, target_cls)
                continue
            structured_instances.append(structured_instance)
        return structured_instances

    @functools.cached_property
    def _session_converter(self) -> cattrs.Converter:
        """Create and return a session converter.

        :return: A `cattrs.Converter` that can convert a dictionary into
          a `europython.Session` instance.
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(arrow.Arrow, lambda raw_dt, _: arrow.get(raw_dt))
        return converter

    async def fetch_session_details(self, code: str) -> tuple[yarl.URL, str]:
        """Fetch session information from the PyCon/PyData website.

        :param code: The session identifier code, as used by pretalx
        :return: A tuple with the session slug and audience experience level
        """
        website_base_url = self.config.pretalx_talk_url  # conference_website_session_base_url
        session_url = yarl.URL(website_base_url.format(code=code)) if code else None

        # there is no API so we crawl the website and search for the
        # 'Python Skill Level' text
        api_base_url = self.config.pretalx_talk_url  # conference_website_api_session_url
        url = api_base_url.format(code=code)
        async with self.session.get(url=url, raise_for_status=True) as response:
            # session_information = await response.json()
            html = await response.text()

        # Find the first occurrence of 'Expected audience expertise: Python:' and then locate the first <p> tag after
        keyword = "Expected audience expertise: Python:"

        keyword_index = html.find(keyword)
        if keyword_index == -1:
            msg = f"The keyword '{keyword}' was not found in the HTML content."
            raise ValueError(msg)

        # Extract the portion of the HTML after 'Python'
        html_after_keyword = html[keyword_index:]

        # Find the first <p> tag and extract the value between <p> and </p>
        start_p = html_after_keyword.find("<p>")
        end_p = html_after_keyword.find("</p>", start_p)
        if start_p == -1 or end_p == -1:
            msg = f"Could not find a <p> tag after '{keyword}' in the HTML content."
            raise ValueError(msg)

        experience = html_after_keyword[start_p + 3 : end_p].strip()

        return session_url, experience

    async def execute_webhook(self, message: discord.WebhookMessage, *, webhook: str) -> None:
        """Execute a Discord webhook.

        :param message: The message to send
        :param webhook: The name of the webhook to execute
        """
        webhook_url = self.config.webhooks[webhook]
        message_data = cattrs.unstructure(message)
        try:
            await self.session.post(url=webhook_url, json=message_data, raise_for_status=True)
        except aiohttp.ClientResponseError as exc:
            # Raise a new exception that does not contain the request
            # URL, as it contains a secret token that should never be
            # logged (without trusting the caller).
            raise exceptions.WebhookDeliveryError(webhook=webhook, status=exc.status, message=exc.message) from None
        _logger.info("Delivered webhook message to webhook %r", webhook)


@attrs.define(frozen=True)
class ScheduleResponse:
    """A response returned by `fetch_sessions`."""

    schedule: europython.Schedule
    from_cache: bool
