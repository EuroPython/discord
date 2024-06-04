"""Exceptions raised as part of the programme notifications cog."""

import attrs


class ApiClientError(Exception):
    """Base class for all api client exceptions."""


@attrs.define
class WebhookDeliveryError(ApiClientError):
    """Raised when delivery to a Discord webhook fails.

    As the webhook url contains a secret token, this exception only
    contains the name of the webhook, the status code, and message.
    """

    webhook: str
    status: int
    message: str

    def __str__(self) -> str:
        """Provide the most important exception information."""
        webhook = self.webhook
        status = self.status
        message = self.message
        return f"Delivery to webhook {webhook!r} failed ({status=}): {message!r}"
