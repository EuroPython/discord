from typing import Any, Protocol
from unittest import mock

from extensions.programme_notifications import configuration
from extensions.programme_notifications.domain import europython


class ClientSessionMockFactory(Protocol):
    """A mocked ClientSession factory."""

    def __call__(self, get_response_content: bytes = b"") -> mock.Mock: ...


class ConfigurationFactory(Protocol):
    """A mocked ClientSession factory."""

    def __call__(
        self, config: dict[str, Any] | None = None
    ) -> configuration.NotifierConfiguration: ...


class SessionFactory(Protocol):
    """Create a session."""

    def __call__(self, **attributes: Any) -> europython.Session: ...
