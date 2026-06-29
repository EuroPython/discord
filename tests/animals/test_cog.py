from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from europython_discord.animals.clients import AnimalClient
from europython_discord.animals.cog import AnimalsCog
from europython_discord.animals.config import AnimalsConfig, AnimalSpecificConfig


@pytest.fixture
def mock_client() -> AnimalClient:
    client = MagicMock(spec=AnimalClient)
    client.fetch_image = AsyncMock(return_value="https://example.com/animal.jpg")
    return client


@pytest.fixture
def config() -> AnimalsConfig:
    return AnimalsConfig(
        channel_name="animal-appreciation",
        cooldown_seconds=10,
        dog=AnimalSpecificConfig(error_messages=["dog error"]),
        cat=AnimalSpecificConfig(error_messages=["cat error"]),
        duck=AnimalSpecificConfig(error_messages=["duck error"]),
        fox=AnimalSpecificConfig(error_messages=["fox error"]),
    )


@pytest.fixture
def cog(mock_client: AnimalClient, config: AnimalsConfig) -> AnimalsCog:
    bot = MagicMock(spec=commands.Bot)
    return AnimalsCog(bot, config, client=mock_client)


@pytest.fixture
def ctx() -> AsyncMock:
    mock = AsyncMock(spec=commands.Context)
    mock.channel.name = "animal-appreciation"
    mock.author = MagicMock()
    mock.author.id = 12345
    mock.send = AsyncMock()
    return mock


@pytest.mark.parametrize("command_name", ["dog_command", "cat_command", "duck_command", "fox_command"])
async def test_animal_commands_success(cog: AnimalsCog, ctx: AsyncMock, command_name: str) -> None:
    command = getattr(cog, command_name)
    await command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert embed.image.url == "https://example.com/animal.jpg"
    assert "friendly" in embed.description


async def test_animal_command_api_error(cog: AnimalsCog, ctx: AsyncMock, mock_client: AnimalClient) -> None:
    mock_client.fetch_image = AsyncMock(return_value=None)

    await cog.dog_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    text = ctx.send.call_args.args[0]
    assert text in cog.config.dog.error_messages


@pytest.mark.parametrize("channel_name", ["wrong-channel", "general", ""])
async def test_animal_command_wrong_channel(cog: AnimalsCog, channel_name: str) -> None:
    ctx = AsyncMock(spec=commands.Context)
    ctx.channel.name = channel_name
    ctx.author = MagicMock()
    ctx.author.id = 12345
    ctx.send = AsyncMock()

    await cog.dog_command.callback(cog, ctx)

    ctx.send.assert_not_awaited()


async def test_animal_command_rate_limit(cog: AnimalsCog, ctx: AsyncMock) -> None:
    # First call succeeds
    await cog.dog_command.callback(cog, ctx)
    assert ctx.send.call_count == 1
    
    # Second call right after fails due to rate limit
    await cog.dog_command.callback(cog, ctx)
    assert ctx.send.call_count == 1  # Still 1, didn't increase
    
    # Fast forward time to bypass cooldown
    import time
    cog._last_usage_timestamp_by_user_id[ctx.author.id] = time.time() - 20
    
    # Third call succeeds
    await cog.dog_command.callback(cog, ctx)
    assert ctx.send.call_count == 2
