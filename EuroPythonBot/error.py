class BotError(Exception):
    """Exception raised for custom bot error."""

    pass


class AlreadyRegisteredError(BotError):
    """Exception raised for registering a registered ticket."""

    pass


class NotFoundError(BotError):
    """Exception raised for ticket not found."""

    pass
