import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands

from europython_discord.cogs.guild_statistics import GuildStatisticsCog
from europython_discord.cogs.ping import PingCog
from europython_discord.configuration import Config
from europython_discord.program_notifications.cog import ProgramNotificationsCog
from europython_discord.registration.cog import RegistrationCog

_logger = logging.getLogger(__name__)


async def run_bot(config: Config, auth_token: str) -> None:
    intents = discord.Intents.all()
    intents.presences = False
    intents.dm_typing = False
    intents.dm_reactions = False
    intents.invites = False
    intents.integrations = False

    async with commands.Bot(intents=intents, command_prefix="$") as bot:
        await bot.add_cog(PingCog(bot))
        await bot.add_cog(RegistrationCog(bot, config))
        await bot.add_cog(ProgramNotificationsCog(bot, config))
        await bot.add_cog(GuildStatisticsCog(bot, config.ROLE_REQUIRED_FOR_STATISTICS))

        await bot.start(auth_token)


def main() -> None:
    parser = argparse.ArgumentParser(description="EuroPython Discord Bot")
    parser.add_argument("--config-file", help="Configuration file (.toml)")
    args = parser.parse_args()

    if not args.config_file and "CONFIG_FILE" not in os.environ:
        raise RuntimeError("Missing option '--config-file' or environment variable 'CONFIG_FILE'")
    config_file = args.config_file or os.environ["CONFIG_FILE"]

    if "DISCORD_BOT_TOKEN" not in os.environ:
        raise RuntimeError("Missing environment variable 'DISCORD_BOT_TOKEN'")
    bot_auth_token = os.environ["DISCORD_BOT_TOKEN"]

    config = Config(Path(config_file))

    logging.basicConfig(
        level=config.LOG_LEVEL,
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        asyncio.run(run_bot(config, auth_token=bot_auth_token))
    except KeyboardInterrupt:
        _logger.info("Received KeyboardInterrupt, exiting...")


if __name__ == "__main__":
    main()
