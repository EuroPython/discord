from datetime import datetime

from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        print(f"{datetime.now()} INFO: Cog 'Ping' ready")

    @commands.hybrid_command(name="ping", description="Ping the bot")
    async def ping_command(self, ctx: commands.Context) -> None:
        print(f"{datetime.now()} INFO: Ping command triggered")
        await ctx.send("Pong!")
