"""Discord bot."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from discord_bot import configuration
from discord_bot.cogs.ping import Ping
from discord_bot.cogs.registration_pydata import RegistrationPyData
from discord_bot.helpers.ticket_connector import TicketOrder

load_dotenv(Path(__file__).resolve().parent.parent / ".secrets")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

_logger = logging.getLogger("bot")


class Bot(commands.Bot):
    """Discord bot class that extends commands.Bot."""

    def __init__(self) -> None:
        """Initialize the bot with specific intents and command prefix."""
        intents = _get_intents()
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)
        self.guild = None
        self.channels = {}

    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        _logger.info("Logged in as user %r (ID=%r)", self.user.name, self.user.id)

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        """Load the extension by name.

        :param name: The name of the extension to load
        :param package: An optional package name for relative imports
        """
        try:
            await super().load_extension(name, package=package)
        except commands.ExtensionError:
            _logger.exception("Failed to load extension %r (package=%r):", name, package)
        else:
            _logger.info("Successfully loaded extension %r (package=%r)", name, package)


def _setup_logging() -> None:
    """Set up a basic logging configuration."""
    config = configuration.Config()

    # Create a stream handler that logs to stdout (12-factor app)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(config.LOG_LEVEL)
    formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)

    # Configure the root logger with the stream handler and log level
    root_logger = logging.getLogger()
    root_logger.addHandler(stream_handler)
    root_logger.setLevel(config.LOG_LEVEL)


def _get_intents() -> discord.Intents:
    """Get the desired intents for the bot."""
    intents = discord.Intents.all()
    intents.presences = False
    intents.dm_typing = False
    intents.dm_reactions = False
    intents.invites = False
    intents.integrations = False
    return intents


async def main() -> None:
    """Main function to run the bot."""
    _setup_logging()
    async with bot:
        await bot.add_cog(Ping(bot))
        await bot.add_cog(RegistrationPyData(bot))
        await bot.load_extension("extensions.programme_notifications")
        await bot.load_extension("extensions.admin")
        # await bot.load_extension("extensions.job_board")
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    bot = Bot()
    orders = TicketOrder()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _logger.info("Received KeyboardInterrupt, exiting...")
