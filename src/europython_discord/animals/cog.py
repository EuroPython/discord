from __future__ import annotations

import logging
import random
import time
from collections import OrderedDict

import discord
from discord.ext import commands

from europython_discord.animals.clients import AnimalClient
from europython_discord.animals.config import ANIMALITY_ANIMALS, AnimalsConfig

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

    async def handle_animal_command(self, ctx: commands.Context, animal: str) -> None:
        if ctx.channel.name != self.config.channel_name:
            return

        if self._is_rate_limited(ctx.author.id):
            return

        result = await self._client.fetch_image(animal)
        if result is None:
            try:
                animal_config = getattr(self.config, animal)
                message = random.choice(animal_config.error_messages)  # noqa: S311
            except AttributeError:
                if self.config.animality_error_messages:
                    plural = f"{animal}s" if animal != "fish" else "fish"
                    message = random.choice(self.config.animality_error_messages).format(  # noqa: S311
                        animal=animal, plural=plural
                    )
                else:
                    message = f"Couldn't find a {animal} picture right now."
            await ctx.send(message)
            return

        embed = discord.Embed()
        embed.description = f"Behold! A friendly {animal} appeared from {result.source}"
        embed.set_image(url=result.url)

        self._update_rate_limit_cache(ctx.author.id)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dog", description="Get a random dog picture")
    async def dog_command(self, ctx: commands.Context) -> None:
        await self.handle_animal_command(ctx, "dog")

    @commands.hybrid_command(name="cat", description="Get a random cat picture")
    async def cat_command(self, ctx: commands.Context) -> None:
        await self.handle_animal_command(ctx, "cat")

    @commands.hybrid_command(name="duck", description="Get a random duck picture")
    async def duck_command(self, ctx: commands.Context) -> None:
        await self.handle_animal_command(ctx, "duck")

    @commands.hybrid_command(name="fox", description="Get a random fox picture")
    async def fox_command(self, ctx: commands.Context) -> None:
        await self.handle_animal_command(ctx, "fox")

    async def cog_load(self) -> None:
        existing = {"dog", "cat", "duck", "fox"}
        for animal in ANIMALITY_ANIMALS:
            if animal in existing:
                continue
            cmd = _make_animality_command(animal, self)
            self.bot.add_command(cmd)

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


def _make_animality_command(name: str, cog: AnimalsCog) -> commands.HybridCommand:
    @commands.hybrid_command(name=name, description=f"Get a random {name} picture")
    async def callback(ctx):  # noqa: ANN001, ANN202
        await cog.handle_animal_command(ctx, name)

    return callback
