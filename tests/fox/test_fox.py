from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from europython_discord.fox.cog import FoxCog
from europython_discord.fox.config import FoxConfig
from europython_discord.fox.foxclient import FoxClient


@pytest.fixture
def mock_client() -> FoxClient:
    client = MagicMock(spec=FoxClient)
    client.fetch_random_fox.return_value = "https://randomfox.ca/images/123.jpg"
    return client


@pytest.fixture
def cog(mock_client: FoxClient) -> FoxCog:
    bot = MagicMock(spec=commands.Bot)
    config = FoxConfig(channel_name="animal-appreciation")
    return FoxCog(bot, config, client=mock_client)


@pytest.fixture
def ctx() -> AsyncMock:
    mock = AsyncMock(spec=commands.Context)
    mock.channel.name = "animal-appreciation"
    mock.send = AsyncMock()
    return mock


async def test_fox_command_success(cog: FoxCog, ctx: AsyncMock) -> None:
    await cog.fox_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert embed.image.url == "https://randomfox.ca/images/123.jpg"
