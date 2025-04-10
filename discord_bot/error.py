"""Custom exceptions for the Discord bot.

This module defines a hierarchy of exceptions used to handle
specific error cases in the bot's functionality.
"""


class BotError(Exception):
    """Exception raised for custom bot error."""


class AlreadyRegisteredError(BotError):
    """Exception raised for registering a registered ticket."""


class NotFoundError(BotError):
    """Exception raised for ticket not found."""
