import logging

from discord.ext import commands

_logger = logging.getLogger(__name__)


class PingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        _logger.info("Cog 'Ping' has been initialized")

    @commands.hybrid_command(name="ping", description="Ping the bot")
    async def ping_command(self, ctx: commands.Context) -> None:
        _logger.debug("The 'ping' command has been triggered!")
        await ctx.send("Pong!")
