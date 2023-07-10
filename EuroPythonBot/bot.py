import asyncio
import logging
import os
import sys
from pathlib import Path

import configuration
from cogs.ping import Ping
from cogs.registration import Registration
from dotenv import load_dotenv
from helpers.pretix_connector import PretixOrder

import discord
from discord.ext import commands

load_dotenv(Path(__file__).resolve().parent.parent / ".secrets")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

_logger = logging.getLogger("bot")


class Bot(commands.Bot):
    def __init__(self):
        intents = _get_intents()
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)
        self.guild = None
        self.channels = dict()

    async def on_ready(self):
        _logger.info("Logged in as user %r (ID=%r)", self.user.name, self.user.id)


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


async def main():
    _setup_logging()
    async with bot:
        await bot.add_cog(Ping(bot))
        await bot.add_cog(Registration(bot))
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    bot = Bot()
    orders = PretixOrder()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _logger.info("Received KeyboardInterrupt, exiting...")
    finally:
        orders.save_registered()
