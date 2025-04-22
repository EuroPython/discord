"""Notify webhooks of sessions."""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, Any, Final

import attrs

from discord_bot.extensions.programme_notifications.domain import discord, europython, services

if TYPE_CHECKING:
    import arrow

    from discord_bot.extensions.programme_notifications import configuration
    from discord_bot.extensions.programme_notifications.services import api, session_information, task_scheduler

_logger = logging.getLogger(f"bot.{__name__}")
_SCHEDULE_NOTIFICATION_MESSAGE: Final = "# Sessions starting in 5 minutes:"
_ROOM_NOTIFICATION_MESSAGE: Final = "# Next up in this room:"
_SCHEDULE_NOTIFICATIONS_LEAD_TIME: Final = datetime.timedelta(minutes=5)
_ROOM_NOTIFICATION_LEAD_TIME: Final = datetime.timedelta(minutes=2)


@attrs.define
class Notifier:
    """Notify webhooks of sessions.

    There are two types of notifications:

    1. Programme notifications with information about all sessions that
       are about to start simultaneously. Sessions are grouped using
       their start time: If sessions start at the same time (minute
       precision), they will be part of the same notification.

    2. Room-specific notifications with information about the session
       that is about to start in a specific room.
    """

    _scheduler: task_scheduler.IScheduler
    _session_information: session_information.SessionInformation
    _api_client: api.IApiClient
    _config: configuration.NotifierConfiguration
    _previous_schedule_hash: str | None = attrs.field(init=False, default=None)

    async def schedule_notifications(self, *, force: bool = False) -> None:
        """Schedule notifications by fetching a new schedule.

        If the fetched schedule has the same hash as the previous
        schedule, the notification tasks will not be refreshed unless
        `force` is `True`.

        :param force: If `True`, the refresh will happen even if the
          fetched schedule has the same hash as the previously fetched
          schedule.
        """
        try:
            response = await self._api_client.fetch_schedule()
        except Exception:
            _logger.exception("Fetching the schedule failed!")
            return

        if not self._should_update(response) and not force:
            _logger.info("No changed schedule available; not rescheduling notifications.")
            return

        new_schedule = response.schedule
        _logger.info("Schedule has changed, updating notifications!")
        self._scheduler.cancel_all()
        sessions = list(services.filter_conference_days(new_schedule.sessions, self._config))
        self._session_information.refresh_from_sessions(sessions)
        grouped_sessions = services.group_sessions_by_minutes(sessions)
        for timeslot, sessions in grouped_sessions.items():
            self._schedule_timeslot_notifications(timeslot, [session.code for session in sessions])
        self._previous_schedule_hash = new_schedule.schedule_hash
        _logger.info("Scheduled notifications!")

    def _should_update(self, api_response: api.ScheduleResponse) -> bool:
        """Check if this response should result in new notifications.

        :param api_response: The API response
        :return: `True` if notifications need to be updated, `False`
          otherwise
        """
        if self._previous_schedule_hash is None:
            # The absence of a hash indicates that there was no schedule
            # yet, which means we should always update.
            _logger.info("No schedule cache yet, we should update the notifications.")
            return True

        if api_response.from_cache:
            # We already have a previous schedule hash, indicating that
            # notifications are in place, so there's no need to fall
            # back to a statically cached version of the schedule that
            # may already be outdated.
            _logger.info(
                "This is a cached schedule response, but we already have notifications in place, so"
                " there's no need to fallback to the cached schedule for notifications."
            )
            return False

        # Only update if the hash of the newly fetched schedule is
        # different from the hash of the schedule that was used to
        # schedule the notifications.
        return self._previous_schedule_hash != api_response.schedule.schedule_hash

    def __len__(self) -> int:
        """Return the number of scheduled notifications."""
        return len(self._scheduler)

    def _schedule_timeslot_notifications(self, timeslot: arrow.Arrow, sessions: list[str]) -> None:
        """Schedule the notifications for this timeslot.

        :param timeslot: The timeslot
        :param sessions: The sessions that start at this timeslot
        """
        # Schedule the combined programme notification
        schedule_notification_at = timeslot - _SCHEDULE_NOTIFICATIONS_LEAD_TIME
        notification_task = self._send_programme_notification(sessions)
        self._scheduler.schedule_tasks_at(notification_task, at=schedule_notification_at)
        # Schedule the individual room notifications
        room_notification_at = timeslot - _ROOM_NOTIFICATION_LEAD_TIME
        room_tasks = (self._send_room_notification(code) for code in sessions)
        self._scheduler.schedule_tasks_at(*room_tasks, at=room_notification_at)

    async def _send_programme_notification(self, session_codes: list[str]) -> None:
        """Send a notification to a schedule notifications webhooks.

        :param session_codes: A list of schedule identifier codes
        """
        sessions = await self._get_sessions(*session_codes)
        notification_tasks = (
            self._send_notification(
                message=_SCHEDULE_NOTIFICATION_MESSAGE,
                sessions=sessions,
                webhook_id=channel.webhook_id,
                include_discord_channel=channel.include_channel_in_embeds,
            )
            for channel in self._config.notification_channels
        )
        results = await asyncio.gather(*notification_tasks, return_exceptions=True)
        _log_gather_exceptions(results, "_send_programme_notification -> _send_notification")

    async def _send_room_notification(self, session_code: str) -> None:
        """Send a notification to an individual room channel.

        :param session_code: The unique identifier code of a session
        """
        sessions = await self._get_sessions(session_code)
        if not sessions:
            _logger.error(
                "Failed to send room notification for session %r: session information is missing!",
                session_code,
            )
            return

        try:
            room_config = self._config.rooms[str(sessions[0].slot.room_id)]
        except KeyError:
            _logger.exception("Failed find a room configuration for session %r", session_code)
            return

        await self._send_notification(
            message=_ROOM_NOTIFICATION_MESSAGE,
            sessions=sessions,
            webhook_id=room_config.webhook_id,
            include_discord_channel=False,
        )

    async def _get_sessions(self, *session_codes: str) -> list[europython.Session]:
        """Fetch sessions from their codes.

        Session codes that result in an exception are ignored.

        :param session_codes: The session codes
        :return: A list of Session instances
        """
        fetch_sessions = (self._session_information.fetch_session(code) for code in session_codes)
        maybe_sessions = await asyncio.gather(*fetch_sessions, return_exceptions=True)
        _log_gather_exceptions(maybe_sessions, "_get_sessions -> fetch_session")
        return [session for session in maybe_sessions if isinstance(session, europython.Session)]

    async def _send_notification(
        self,
        message: str,
        sessions: list[europython.Session],
        webhook_id: str,
        *,
        include_discord_channel: bool = False,
    ) -> None:
        """Send a notification with sessions to a webhook."""
        embeds = [
            services.create_session_embed(
                session=session,
                slido_url=self._config.slido_url,
                conference_name=self._config.conference_name,
                conference_website=self._config.conference_website,
                include_discord_channel=include_discord_channel,
            )
            for session in sessions
        ]
        if not embeds:
            _logger.error("Can't send message with no embeds to webhook %r", webhook_id)
            return
        webhook_message = discord.WebhookMessage(content=message, embeds=embeds)
        await self._api_client.execute_webhook(webhook_message, webhook=webhook_id)


def _log_gather_exceptions(results: list[Any], operation: str) -> None:
    """Log exceptions returned in an `asyncio.gather` operation.

    :param results: The `gather` results
    """
    errors = [result for result in results if isinstance(result, Exception)]
    if not errors:
        return
    _logger.error(
        "At least one exception occurred during operation %r",
        operation,
        exc_info=ExceptionGroup(f"Exceptions raised during {operation!r}", errors),
    )
