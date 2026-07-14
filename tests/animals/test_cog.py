from unittest.mock import AsyncMock, MagicMock

from discord.ext import commands
from discord.ext.commands import Context

from europython_discord.animals.cog import AnimalsCog
from europython_discord.animals.config import AnimalsConfig
from europython_discord.animals.providers import AnimalImageProvider
from europython_discord.animals.providers.animal_image_provider import AnimalImage
from europython_discord.animals.rate_limiter import RateLimiter

DEFAULT_CHANNEL_NAME = "animal-channel"
DEFAULT_AUTHOR_ID = 12345
DEFAULT_ANIMAL = "cat"
DEFAULT_IMAGE_URL = "https://example.com/cat.jpg"
DEFAULT_IMAGE_SOURCE = "https://example.com"


class FakeProvider(AnimalImageProvider):
    async def generate_image(self) -> AnimalImage | None:
        return AnimalImage(url=DEFAULT_IMAGE_URL, source=DEFAULT_IMAGE_SOURCE)


class FakeConfig(AnimalsConfig):
    channel_name: str = "animal-appreciation"
    cooldown_seconds: int = 10


def create_fake_cog(
    bot: commands.Bot | None = None,
    providers_by_animal: dict[str, list[AnimalImageProvider]] | None = None,
    rate_limiter: RateLimiter | None = None,
    channel_name: str = DEFAULT_CHANNEL_NAME,
) -> AnimalsCog:
    providers = {DEFAULT_ANIMAL: [FakeProvider()]}
    return AnimalsCog(
        bot=MagicMock() if bot is None else bot,
        channel_name=channel_name,
        providers_by_animal=providers if providers_by_animal is None else providers_by_animal,
        rate_limiter=RateLimiter(cooldown_seconds=10) if rate_limiter is None else rate_limiter,
    )


def create_fake_context(
    channel_name: str = DEFAULT_CHANNEL_NAME,
    author_id: int = DEFAULT_AUTHOR_ID,
) -> Context:
    context = AsyncMock(spec=commands.Context)
    context.author.id = author_id
    context.channel.name = channel_name
    context.send = AsyncMock()
    context.defer = AsyncMock()
    # Provide a synchronous guild.channels list so discord.utils.get works.
    guild = MagicMock()
    fake_channel = MagicMock()
    fake_channel.name = DEFAULT_CHANNEL_NAME
    fake_channel.mention = f"#{DEFAULT_CHANNEL_NAME}"
    guild.channels = [fake_channel]
    context.guild = guild
    return context


async def test_command_success() -> None:
    cog = create_fake_cog()
    ctx = create_fake_context()

    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx)

    ctx.defer.assert_awaited_once()
    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert embed.image.url == DEFAULT_IMAGE_URL
    assert embed.description == f"Behold! A friendly cat appeared from {DEFAULT_IMAGE_SOURCE}"


async def test_command_wrong_channel() -> None:
    cog = create_fake_cog(channel_name=DEFAULT_CHANNEL_NAME)
    ctx = create_fake_context(channel_name="some-other-channel")

    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx)

    ctx.defer.assert_awaited_once()
    ctx.send.assert_awaited_once()
    (message,) = ctx.send.call_args.args
    assert message == f"This command can only be used in #{DEFAULT_CHANNEL_NAME}."


async def test_rate_limiting() -> None:
    cog = create_fake_cog(rate_limiter=RateLimiter(cooldown_seconds=10))

    # first call
    ctx_1 = create_fake_context()
    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx_1)
    ctx_1.send.assert_awaited_once()
    assert "embed" in ctx_1.send.call_args.kwargs

    # second call with same user - rate limited, ephemeral error message
    ctx_2 = create_fake_context()
    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx_2)
    ctx_2.send.assert_awaited_once()
    (message,) = ctx_2.send.call_args.args
    assert message == "You are being rate limited. Please try again later."


async def test_rate_limiting_different_user() -> None:
    cog = create_fake_cog(rate_limiter=RateLimiter(cooldown_seconds=10))

    # first call
    ctx_1 = create_fake_context(author_id=111)
    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx_1)
    ctx_1.send.assert_awaited_once()

    # second call with different user
    ctx_2 = create_fake_context(author_id=222)
    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx_2)
    ctx_2.send.assert_awaited_once()


async def test_rate_limiting_after_cooldown_period() -> None:
    rate_limiter = RateLimiter(cooldown_seconds=10)
    cog = create_fake_cog(rate_limiter=rate_limiter)

    # first call
    ctx_1 = create_fake_context()
    rate_limiter.get_current_timestamp = lambda: 60
    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx_1)
    ctx_1.send.assert_awaited_once()

    # second call with same user after 15 seconds
    ctx_2 = create_fake_context()
    rate_limiter.get_current_timestamp = lambda: 75
    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx_2)
    ctx_2.send.assert_awaited_once()


async def test_provider_error() -> None:
    class BrokenProvider(AnimalImageProvider):
        async def generate_image(self) -> AnimalImage | None:
            raise RuntimeError("Boom!")

    cog = create_fake_cog(providers_by_animal={DEFAULT_ANIMAL: [BrokenProvider()]})
    ctx = create_fake_context()

    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx)

    ctx.send.assert_called_once()
    (message,) = ctx.send.call_args.args
    assert message == f"Failed to fetch {DEFAULT_ANIMAL} picture. Internal error, please report it."


async def test_provider_unsuccessful() -> None:
    class BrokenProvider(AnimalImageProvider):
        async def generate_image(self) -> AnimalImage | None:
            return None

    cog = create_fake_cog(providers_by_animal={DEFAULT_ANIMAL: [BrokenProvider()]})
    ctx = create_fake_context()

    await cog.post_animal_picture(DEFAULT_ANIMAL, ctx=ctx)

    ctx.send.assert_called_once()
    (message,) = ctx.send.call_args.args
    assert message == (
        f"Failed to fetch {DEFAULT_ANIMAL} picture. If this happens repeatedly, please report it."
    )
    assert ctx.send.call_args.kwargs.get("ephemeral") is True
