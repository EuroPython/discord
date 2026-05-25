from __future__ import annotations

import logging
import random

import discord
from discord.ext import commands

from europython_discord.dog.config import DogConfig
from europython_discord.dog.dogclient import DogClient

_logger = logging.getLogger(__name__)


class DogCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        config: DogConfig,
        client: DogClient | None = None,
    ) -> None:
        self.bot = bot
        self.config = config
        self._client = client or DogClient()
        _logger.info("Cog 'Dog' has been initialized")

    @commands.hybrid_command(name="dog", description="Get a random dog picture")
    async def dog_command(self, ctx: commands.Context) -> None:
        image_url = await self._client.fetch_random_dog()
        if image_url is None:
            message = random.choice(self.config.error_messages)  # noqa: S311
            await ctx.send(message)
            return

        embed = discord.Embed()
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)
