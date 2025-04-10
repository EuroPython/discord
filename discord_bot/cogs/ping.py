"""Ping command for the bot."""

import logging

from discord.ext import commands

_logger = logging.getLogger(f"bot.{__name__}")


class Ping(commands.Cog):
    """Ping command for the bot."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the Ping cog."""
        self.bot: commands.Bot = bot
        _logger.info("Cog 'Ping' has been initialized")

    @commands.hybrid_command(name="ping", description="Ping the bot")
    async def ping_command(self, ctx: commands.Context) -> None:
        """Ping the bot and respond with 'Pong!'."""
        _logger.debug("The 'ping' command has been triggered!")
        await ctx.send("Pong!")
