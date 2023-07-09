import asyncio
import os
from datetime import datetime
from pathlib import Path

from cogs.ping import Ping
from cogs.registration import Registration
from dotenv import load_dotenv
from helpers.pretix_connector import PretixOrder

import discord
from discord.ext import commands

load_dotenv(Path("__file__").absolute().parent.joinpath(".secrets"))
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)
        self.guild = None
        self.channels = dict()

    async def on_ready(self):
        print(f"{datetime.now()} INFO: Loggedin as {self.user} (ID: {self.user.id})")


async def main():
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
        print("Keyboard Interrupt. Exiting...")
    finally:
        orders.save_registered()
