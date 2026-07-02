from __future__ import annotations

import logging
import random
import time
from collections import OrderedDict

import discord
from discord.ext import commands

from europython_discord.animals.clients import AnimalClient
from europython_discord.animals.config import AnimalsConfig

_logger = logging.getLogger(__name__)

_MAX_COOLDOWN_TRACKING = 100


class AnimalsCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        config: AnimalsConfig,
        client: AnimalClient | None = None,
    ) -> None:
        self.bot = bot
        self.config = config
        self._client = client or AnimalClient()
        self._last_usage_timestamp_by_user_id: OrderedDict[int, float] = OrderedDict()
        _logger.info("Cog 'Animals' has been initialized")

    async def _handle_animal_command(
        self, ctx: commands.Context, animal: str, source_url: str
    ) -> None:
        if ctx.channel.name != self.config.channel_name:
            return

        if self._is_rate_limited(ctx.author.id):
            return

        image_url = await self._client.fetch_image(animal)
        if image_url is None:
            # Get the error messages for this specific animal
            animal_config = getattr(self.config, animal)
            message = random.choice(animal_config.error_messages)  # noqa: S311
            await ctx.send(message)
            return

        embed = discord.Embed()
        embed.description = f"Behold! A friendly {animal} appeared from {source_url}"
        embed.set_image(url=image_url)

        self._update_rate_limit_cache(ctx.author.id)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dog", description="Get a random dog picture")
    async def dog_command(self, ctx: commands.Context) -> None:
        await self._handle_animal_command(ctx, "dog", "https://dog.ceo")

    @commands.hybrid_command(name="cat", description="Get a random cat picture")
    async def cat_command(self, ctx: commands.Context) -> None:
        await self._handle_animal_command(ctx, "cat", "https://cataas.com")

    @commands.hybrid_command(name="duck", description="Get a random duck picture")
    async def duck_command(self, ctx: commands.Context) -> None:
        await self._handle_animal_command(ctx, "duck", "https://random-d.uk")

    @commands.hybrid_command(name="fox", description="Get a random fox picture")
    async def fox_command(self, ctx: commands.Context) -> None:
        await self._handle_animal_command(ctx, "fox", "https://randomfox.ca/floof/")

    def _is_rate_limited(self, user_id: int) -> bool:
        last_usage_timestamp = self._last_usage_timestamp_by_user_id.get(user_id, 0)
        return last_usage_timestamp + self.config.cooldown_seconds > time.time()

    def _update_rate_limit_cache(self, user_id: int) -> None:
        # update cache
        self._last_usage_timestamp_by_user_id[user_id] = time.time()

        # trim cache
        self._last_usage_timestamp_by_user_id.move_to_end(user_id)
        if len(self._last_usage_timestamp_by_user_id) > _MAX_COOLDOWN_TRACKING:
            self._last_usage_timestamp_by_user_id.popitem(last=False)
