from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from europython_discord.cat.cog import CatCog
from europython_discord.cat.config import CatConfig
from europython_discord.cat.catclient import CatClient


@pytest.fixture
def mock_client() -> CatClient:
    client = MagicMock(spec=CatClient)
    client.fetch_random_cat.return_value = "https://cataas.com/cat/mockid"
    return client


@pytest.fixture
def cog(mock_client: CatClient) -> CatCog:
    bot = MagicMock(spec=commands.Bot)
    config = CatConfig(channel_name="animal-appreciation")
    return CatCog(bot, config, client=mock_client)


@pytest.fixture
def ctx() -> AsyncMock:
    mock = AsyncMock(spec=commands.Context)
    mock.channel.name = "animal-appreciation"
    mock.send = AsyncMock()
    return mock


async def test_cat_command_success(cog: CatCog, ctx: AsyncMock) -> None:
    await cog.cat_command.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert embed.image.url == "https://cataas.com/cat/mockid"
