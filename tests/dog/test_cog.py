from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from europython_discord.dog.cog import DogCog
from europython_discord.dog.config import DogConfig
from europython_discord.dog.dogclient import DogClient


@pytest.fixture
def config() -> DogConfig:
    return DogConfig()


@pytest.fixture
def bot() -> MagicMock:
    return MagicMock(spec=commands.Bot)


@pytest.fixture
def dog_url() -> str:
    return "https://images.dog.ceo/dog.jpg"


@pytest.fixture
def mock_client(dog_url: str) -> DogClient:
    client = MagicMock(spec=DogClient)
    client.fetch_random_dog.return_value = dog_url
    return client


@pytest.fixture
def cog(bot: MagicMock, config: DogConfig, mock_client: DogClient) -> DogCog:
    return DogCog(bot, config, client=mock_client)


@pytest.fixture
def ctx() -> AsyncMock:
    mock = AsyncMock(spec=commands.Context)
    mock.send = AsyncMock()
    return mock


async def test_dog_command_success(cog: DogCog, ctx: AsyncMock, dog_url: str) -> None:
    await cog.dog_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert embed.image.url == dog_url


async def test_dog_command_api_error(cog: DogCog, ctx: AsyncMock, mock_client: DogClient) -> None:
    mock_client.fetch_random_dog.return_value = None

    await cog.dog_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    text = ctx.send.call_args.args[0]

    assert text in cog.config.error_messages
