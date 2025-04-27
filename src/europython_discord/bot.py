import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from europython_discord.cogs.guild_statistics import GuildStatisticsCog
from europython_discord.cogs.ping import PingCog
from europython_discord.configuration import Config
from europython_discord.program_notifications.cog import ProgramNotificationsCog
from europython_discord.registration.cog import RegistrationCog

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".secrets")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

_logger = logging.getLogger(__name__)


async def run_bot(config: Config) -> None:
    intents = discord.Intents.all()
    intents.presences = False
    intents.dm_typing = False
    intents.dm_reactions = False
    intents.invites = False
    intents.integrations = False

    async with commands.Bot(intents=intents, command_prefix="$") as bot:
        await bot.add_cog(PingCog(bot))
        await bot.add_cog(RegistrationCog(bot))
        await bot.add_cog(ProgramNotificationsCog(bot))
        await bot.add_cog(GuildStatisticsCog(bot, config.ROLE_REQUIRED_FOR_STATISTICS))
        await bot.start(DISCORD_BOT_TOKEN)


def main() -> None:
    config = Config()

    logging.basicConfig(
        level=config.LOG_LEVEL,
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        asyncio.run(run_bot(config))
    except KeyboardInterrupt:
        _logger.info("Received KeyboardInterrupt, exiting...")


if __name__ == "__main__":
    main()
