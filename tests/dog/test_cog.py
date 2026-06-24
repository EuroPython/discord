from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from europython_discord.dog.cog import DogCog
from europython_discord.dog.config import DogConfig
from europython_discord.dog.dogclient import DogClient


@pytest.fixture
def config() -> DogConfig:
    return DogConfig(channel_name="animal-appreciation")


@pytest.fixture
def bot() -> MagicMock:
    return MagicMock(spec=commands.Bot)


@pytest.fixture
def mock_client() -> DogClient:
    client = MagicMock(spec=DogClient)
    client.fetch_random_dog.return_value = "https://images.dog.ceo/dog.jpg"
    return client


@pytest.fixture
def cog(bot: MagicMock, config: DogConfig, mock_client: DogClient) -> DogCog:
    return DogCog(bot, config, client=mock_client)


@pytest.fixture
def ctx() -> AsyncMock:
    mock = AsyncMock(spec=commands.Context)
    mock.channel.name = "animal-appreciation"
    mock.send = AsyncMock()
    return mock


async def test_dog_command_success(cog: DogCog, ctx: AsyncMock) -> None:
    await cog.dog_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert embed.image.url == "https://images.dog.ceo/dog.jpg"


async def test_dog_command_api_error(cog: DogCog, ctx: AsyncMock, mock_client: DogClient) -> None:
    mock_client.fetch_random_dog.return_value = None

    await cog.dog_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    text = ctx.send.call_args.args[0]

    assert text in cog.config.error_messages


@pytest.mark.parametrize(
    "channel_name",
    ["wrong-channel", "general", ""],
)
async def test_dog_command_wrong_channel(cog: DogCog, channel_name: str) -> None:
    ctx = AsyncMock(spec=commands.Context)
    ctx.channel.name = channel_name
    ctx.send = AsyncMock()

    await cog.dog_command.callback(cog, ctx)

    ctx.send.assert_not_awaited()
