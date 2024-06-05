"""An API client to query session information.

Detailed session information is fetched from two different sources, the
Pretalx API and the EuroPython API. This API-client provides an
abstraction layer in which the caller does not have to care about the
actual endpoint that gets polled.
"""

import functools
import hashlib
import json
import logging
import pathlib
from collections.abc import Iterable
from typing import Any, Protocol, TypeVar

import aiohttp
import arrow
import attrs
import cattrs
import yarl
from attrs import validators

from extensions.programme_notifications import configuration, exceptions
from extensions.programme_notifications.domain import discord, europython

_DEFAULT_SCHEDULE_CACHE_PATH: pathlib.Path = (
    pathlib.Path(__file__).resolve().parent / "_cached" / "schedule.json"
)
_logger = logging.getLogger(f"bot.{__name__}")
_T = TypeVar("_T")


class IApiClient(Protocol):
    """Protocol for an API client."""

    async def fetch_schedule(self) -> "ScheduleResponse":
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
    def _cache_path_exists_validator(self, attribute: str, value: pathlib.Path):
        """Validate that the schedule cache path exists."""
        del attribute  # unused
        if not value.exists():
            raise ValueError("The path '%s' does not exist!")

    async def fetch_schedule(self) -> "ScheduleResponse":
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
            schedule_hash=hashlib.sha1(response_content).hexdigest(),
        )
        return ScheduleResponse(schedule=schedule, from_cache=from_cache)

    async def _fetch_schedule(self, url: str) -> bytes:
        """Fetch the schedule from Pretalx."""
        _logger.info("Making call to Pretalx API.")
        async with self.session.get(url=url, raise_for_status=True) as response:
            response_content = await response.read()
        return response_content

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
        """Fetch session information from the EuroPython API.

        :param code: The session identifier code, as used by EuroPython
        :return: A tuple with the session slug and audience experience
          level
        """
        api_base_url = self.config.europython_api_session_url
        url = api_base_url.format(code=code)
        async with self.session.get(url=url, raise_for_status=True) as response:
            session_information = await response.json()

        slug = session_information["session"].get("slug")
        website_base_url = self.config.europython_session_base_url
        session_url = yarl.URL(website_base_url.format(slug=slug)) if slug else None
        return session_url, session_information["session"].get("experience")

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
            raise exceptions.WebhookDeliveryError(
                webhook=webhook, status=exc.status, message=exc.message
            ) from None
        _logger.info("Delivered webhook message to webhook %r", webhook)


@attrs.define(frozen=True)
class ScheduleResponse:
    """A response returned by `fetch_sessions`."""

    schedule: europython.Schedule
    from_cache: bool
