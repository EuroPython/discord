from __future__ import annotations

import logging
import random
from typing import Self

import discord
from discord.ext import commands

from europython_discord.animals import providers
from europython_discord.animals.config import AnimalsConfig
from europython_discord.animals.providers import AnimalImageProvider
from europython_discord.animals.rate_limiter import RateLimiter

_logger = logging.getLogger(__name__)


class AnimalsCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        providers_by_animal: dict[str, list[AnimalImageProvider]],
        rate_limiter: RateLimiter,
        channel_name: str,
    ) -> None:
        self._bot = bot
        self._channel_name = channel_name
        self._providers = providers_by_animal
        self._rate_limiter = rate_limiter

        for animal in self._providers:
            self._bot.add_command(self._create_animal_command(animal))

        _logger.info("Cog 'Animals' has been initialized")

    async def post_animal_picture(self, animal: str, ctx: commands.Context) -> None:
        if ctx.channel.name != self._channel_name:
            return
        if self._rate_limiter.is_rate_limited(ctx.author.id):
            return
        if animal not in self._providers:
            return

        provider = random.choice(self._providers[animal])  # noqa: S311 suspicious-non-cryptographic-random-usage
        try:
            image = await provider.generate_image()
        except Exception:
            _logger.exception("Error while generating %s image", animal)
            await ctx.send(f"Failed to fetch {animal} picture. Internal error, please report it.")
            return

        if image is None:
            _logger.error("Failed to fetch %s pictures", animal)
            await ctx.send(f"Failed to fetch {animal} picture.")
            return

        embed = discord.Embed()
        embed.description = f"Behold! A friendly {animal} appeared from {image.source}"
        embed.set_image(url=image.url)
        self._rate_limiter.register_usage(ctx.author.id)
        await ctx.send(embed=embed)

    def _create_animal_command(self, animal: str) -> commands.HybridCommand:
        @commands.hybrid_command(name=animal, description=f"Get a random {animal} picture")
        async def callback(ctx: commands.Context) -> None:
            await self.post_animal_picture(animal, ctx)

        return callback

    @classmethod
    def from_config(cls, bot: commands.Bot, config: AnimalsConfig) -> Self:
        return cls(
            bot=bot,
            providers_by_animal=providers.get_all_providers(),
            rate_limiter=RateLimiter(config.cooldown_seconds),
            channel_name=config.channel_name,
        )
