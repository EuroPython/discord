import asyncio
import os

from dotenv import load_dotenv

import discord
from cogs.ping import Ping
from discord.ext import commands

from pathlib import Path

load_dotenv(Path("__file__").absolute().parent.joinpath(".secrets"))
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned_or("$"), intents=intents
        )
        self.guild = None
        self.channels = dict()

    async def on_ready(self):
        print(f"Loggedin as {self.user} (ID: {self.user.id})")


async def main():
    async with bot:
        await bot.add_cog(Ping(bot))
        await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    bot = Bot()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting...")
