"""A repository for EuroPython sessions."""

import logging
from collections.abc import Sized
from typing import Protocol

import attrs

from . import europython

_log = logging.getLogger(f"bot.{__name__}")


class ISessionRepository(Sized, Protocol):
    """A protocol for a session repository."""

    def get(self, code: str) -> europython.Session:
        """Get a EuroPython session by its session code.

        :param code: The unique session identifier code
        :return: A `europython.Session` instance
        """

    def add(self, session: europython.Session) -> None:
        """Add a new session to the repository.

        :param session: A session to add to the repository
        """

    def clear(self) -> None:
        """Clear the session repository."""


@attrs.define
class SessionRepository:
    """An in-memory EuroPython session repository."""

    _sessions: dict[str, europython.Session] = attrs.field(default=attrs.Factory(dict))

    def __len__(self) -> int:
        """Get the number of sessions in the repository."""
        return len(self._sessions)

    def get(self, code: str) -> europython.Session:
        """Get a EuroPython session by its session code.

        :param code: The unique session identifier code
        :return: A `europython.Session` instance
        """
        return self._sessions[code]

    def add(self, session: europython.Session) -> None:
        """Add a new session to the repository.

        :param session: A session to add to the repository
        """
        self._sessions[session.code] = session
        _log.debug("Added session %r to the session repository", session.code)

    def clear(self) -> None:
        """Clear the session repository."""
        self._sessions = {}
        _log.info("Cleared the session repository!")
