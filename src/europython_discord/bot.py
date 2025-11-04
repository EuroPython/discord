from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Literal

import discord
from discord.ext import commands
from pydantic import BaseModel

from europython_discord.cogs.guild_statistics import GuildStatisticsCog, GuildStatisticsConfig
from europython_discord.cogs.ping import PingCog
from europython_discord.program_notifications.cog import ProgramNotificationsCog
from europython_discord.program_notifications.config import ProgramNotificationsConfig
from europython_discord.registration.cog import RegistrationCog
from europython_discord.registration.config import RegistrationConfig

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# silence warning about missing discord voice support
# https://github.com/Rapptz/discord.py/issues/1719#issuecomment-437703581
discord.VoiceClient.warn_nacl = False

_logger = logging.getLogger(__name__)


class Config(BaseModel):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    registration: RegistrationConfig
    program_notifications: ProgramNotificationsConfig
    guild_statistics: GuildStatisticsConfig


async def run_bot(config: Config, auth_token: str) -> None:
    intents = discord.Intents.all()
    intents.presences = False
    intents.dm_typing = False
    intents.dm_reactions = False
    intents.invites = False
    intents.integrations = False

    async with commands.Bot(intents=intents, command_prefix="$") as bot:
        await bot.add_cog(PingCog(bot))
        await bot.add_cog(RegistrationCog(bot, config.registration))
        await bot.add_cog(ProgramNotificationsCog(bot, config.program_notifications))
        await bot.add_cog(GuildStatisticsCog(bot, config.guild_statistics))

        await bot.start(auth_token)


def main() -> None:
    parser = argparse.ArgumentParser(description="PyLadiesCon Discord Bot")
    parser.add_argument("--config-file", type=Path, required=True, help="Configuration file")
    args = parser.parse_args()

    if "DISCORD_BOT_TOKEN" not in os.environ:
        raise RuntimeError("Missing environment variable 'DISCORD_BOT_TOKEN'")
    bot_auth_token = os.environ["DISCORD_BOT_TOKEN"]

    config_file_content = args.config_file.read_text()
    config = Config(**tomllib.loads(config_file_content))

    logging.basicConfig(
        level=config.log_level,
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        asyncio.run(run_bot(config, auth_token=bot_auth_token))
    except KeyboardInterrupt:
        _logger.info("Received KeyboardInterrupt, exiting...")


if __name__ == "__main__":
    main()
