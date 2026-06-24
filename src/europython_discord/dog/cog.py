from __future__ import annotations

import logging
import random
import time
from collections import OrderedDict

import discord
from discord.ext import commands

from europython_discord.dog.config import DogConfig
from europython_discord.dog.dogclient import DogClient

_logger = logging.getLogger(__name__)

_MAX_COOLDOWN_TRACKING = 100


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
        self._last_used: OrderedDict[int, float] = OrderedDict()
        _logger.info("Cog 'Dog' has been initialized")

    @commands.hybrid_command(name="dog", description="Get a random dog picture")
    async def dog_command(self, ctx: commands.Context) -> None:
        if ctx.channel.name != self.config.channel_name:
            return

        if self._is_rate_limited(ctx.author.id):
            return

        if (image_url := await self._client.fetch_random_dog()) is None:
            message = random.choice(self.config.error_messages)  # noqa: S311
            await ctx.send(message)
            return

        embed = discord.Embed()
        embed.description = "A random dog image"
        embed.set_image(url=image_url)
        embed.set_footer(text="Powered by dog.ceo")

        self._update_rate_limit_cache(ctx.author.id)
        await ctx.send(embed=embed)

    def _is_rate_limited(self, user_id: int) -> bool:
        last = self._last_used.get(user_id)
        return bool(last is not None and time.time() - last < self.config.cooldown_seconds)

    def _update_rate_limit_cache(self, user_id: int) -> None:
        self._last_used[user_id] = time.time()
        self._last_used.move_to_end(user_id)
        if len(self._last_used) > _MAX_COOLDOWN_TRACKING:
            self._last_used.popitem(last=False)
