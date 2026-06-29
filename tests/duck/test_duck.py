from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from europython_discord.duck.cog import DuckCog
from europython_discord.duck.config import DuckConfig
from europython_discord.duck.duckclient import DuckClient


@pytest.fixture
def mock_client() -> DuckClient:
    client = MagicMock(spec=DuckClient)
    client.fetch_random_duck.return_value = "https://random-d.uk/api/randomimg?t=123"
    return client


@pytest.fixture
def cog(mock_client: DuckClient) -> DuckCog:
    bot = MagicMock(spec=commands.Bot)
    config = DuckConfig(channel_name="animal-appreciation")
    return DuckCog(bot, config, client=mock_client)


@pytest.fixture
def ctx() -> AsyncMock:
    mock = AsyncMock(spec=commands.Context)
    mock.channel.name = "animal-appreciation"
    mock.send = AsyncMock()
    return mock


async def test_duck_command_success(cog: DuckCog, ctx: AsyncMock) -> None:
    await cog.duck_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert embed.image.url == "https://random-d.uk/api/randomimg?t=123"
