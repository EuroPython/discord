import logging
import os

import attrs
import yarl

from .. import configuration, exceptions
from ..domain import europython, repositories
from . import api

_logger = logging.getLogger(f"bot.{__name__}")


@attrs.define
class SessionInformation:
    """A service to fetch session information."""

    _session_repository: repositories.ISessionRepository
    _api_client: api.IApiClient
    _config: configuration.NotifierConfiguration

    async def fetch_session(self, code: str) -> europython.Session:
        """Fetch the session.

        Not all session information is available in the original Pretalx
        API response. If additional session information is unavailable
        in the session instance retrieved from the repository, the
        additional information is fetched from the EuroPython API.

        :param code: The identifier code of the session
        :return: A session instance
        """
        session = self._session_repository.get(code)
        if session.url is None or session.experience is None:
            try:
                session.url, session.experience = await self._api_client.fetch_session_details(code)
            except Exception:
                _logger.exception("Fetching addition session details failed!")

        session.livestream_url = self._get_livestream_url(session)
        session.discord_channel_id = self._get_discord_channel_id(session)
        session.survey_url = self._get_survey_url(session)
        return session

    async def _fetch_session_details(self, code: str) -> tuple[yarl.URL | None, str | None]:
        """Fetch session details using the API client.

        :param code: The identifier code
        :return: The session URL and the audience experience level
        """
        try:
            url, experience = await self._api_client.fetch_session_details(session_id=code)
        except exceptions.ApiClientError:
            _logger.exception("Failed to retrieve session detail information for session %r", code)
            return None, None

        return url, experience

    def _get_livestream_url(self, session: europython.Session) -> yarl.URL | None:
        """Get the livestream env var name for this session from the config and then get the
        livestream url from the env var.

        :param session: The session
        :return: The livestream URL or None
        """
        date = session.slot.start.strftime("%Y-%m-%d")
        try:
            env_var_name = self._config.rooms[str(session.slot.room_id)].livestreams[date]
            livestream_url = os.getenv(env_var_name)
            if livestream_url:
                return yarl.URL(livestream_url)
            return None
        except (KeyError, AttributeError):
            return

    def _get_discord_channel_id(self, session: europython.Session) -> str | None:
        """Get the discord channel id for this session

        :param session: The session
        :return: The discord channel id for the room or None
        """
        try:
            return self._config.rooms[str(session.slot.room_id)].discord_channel_id
        except (KeyError, AttributeError):
            return

    def _get_survey_url(self, session: europython.Session) -> str | None:
        """Get the survey url for this session.

        :param session: The session
        :return: The livestream URL or None
        """
        try:
            return self._config.rooms[str(session.slot.room_id)].survey_url
        except (KeyError, AttributeError):
            return

    def refresh_from_sessions(self, sessions: list[europython.Session]) -> None:
        """Refresh from a list of sessions

        :param sessions: The schedule to use
        """
        session_repository = self._session_repository.__class__()
        for session in sessions:
            session_repository.add(session)
        self._session_repository = session_repository
        _logger.info("Sessions refreshed. Added %r sessions to the repository.", len(sessions))
