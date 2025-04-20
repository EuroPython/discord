"""Script to export all guild members and their roles to per-guild .csv files."""

import argparse
import asyncio
import csv
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext.commands import Bot

logger = logging.getLogger(__name__)

DESCRIPTION = """\
Export all guild members and their roles to per-guild .csv files.

Requires the environment variable 'BOT_TOKEN' to be set.
Requires bot privileges for receiving 'GUILD_MEMBER' events.
"""


def write_members_to_csv_file(guild: discord.Guild, output_file: Path) -> None:
    """Write all guild members and their roles to a .csv files."""
    guild_roles = [role for role in guild.roles if role.name != "@everyone"]

    entries = []
    for member in guild.members:
        member_role_ids = {role.id for role in member.roles if role.name != "@everyone"}
        entries.append(
            {
                "guild_id": guild.id,
                "guild_name": guild.name,
                "member_id": member.id,
                "member_name": member.name,
                "member_nickname": member.display_name,
                **{role.name: "x" if role.id in member_role_ids else "" for role in guild_roles},
            }
        )

    with output_file.open("w") as fp:
        writer = csv.DictWriter(fp, fieldnames=entries[0].keys(), dialect="unix")
        writer.writeheader()
        writer.writerows(entries)


class MemberExportBot(Bot):
    def __init__(self, output_dir: Path) -> None:
        """Discord bot which exports all guild members to .csv files and then stops itself."""
        super().__init__(
            intents=discord.Intents(guilds=True, members=True),
            command_prefix="$",
        )

        self.__output_dir = output_dir

    async def on_ready(self) -> None:
        """Event handler for successful connection."""
        self.__output_dir.mkdir(exist_ok=True)
        for guild in self.guilds:
            output_file = self.__output_dir / f"{guild.id}-members.csv"
            write_members_to_csv_file(guild, output_file)

        await self.close()

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Event handler for uncaught exceptions."""
        exc_type, exc_value, _exc_traceback = sys.exc_info()
        logger.error(f"{exc_type.__name__} {exc_value}")

        # let discord.py log the exception
        await super().on_error(event, *args, **kwargs)

        await self.close()


async def run_bot(bot: Bot, token: str) -> None:
    """Run a Discord bot."""
    async with bot as _bot:
        try:
            await _bot.login(token)
            await _bot.connect()
        except discord.LoginFailure:
            logger.exception("Invalid Discord bot token")
        except discord.PrivilegedIntentsRequired:
            logger.exception("Insufficient privileges. Required events: 'GUILD_MEMBERS'")


def main():
    """Run this application."""
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("output_dir", type=Path, help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Enable logging")
    args = parser.parse_args()

    bot_token = os.getenv("BOT_TOKEN")
    if bot_token is None:
        raise RuntimeError("'BOT_TOKEN' environment variable is not set")

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    bot = MemberExportBot(args.output_dir)
    asyncio.run(run_bot(bot, bot_token))


if __name__ == "__main__":
    main()
