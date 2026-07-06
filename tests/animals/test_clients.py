from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession

from europython_discord.animals.clients import AnimalClient, ImageResult


@pytest.fixture
async def client() -> AnimalClient:
    c = AnimalClient()
    yield c
    await c._session.close()


async def test_fetch_dog(client: AnimalClient) -> None:
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={"message": "https://images.dog.ceo/dog.jpg", "status": "success"}
    )
    mock_response.raise_for_status = MagicMock()

    mock_get = MagicMock()
    mock_get.return_value.__aenter__.return_value = mock_response

    with patch.object(ClientSession, "get", mock_get):
        result = await client.fetch_image("dog")

    assert result == ImageResult("https://images.dog.ceo/dog.jpg", "https://dog.ceo")
    mock_get.assert_called_once()


async def test_fetch_cat(client: AnimalClient) -> None:
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"url": "/cat/mockid"})
    mock_response.raise_for_status = MagicMock()

    mock_get = MagicMock()
    mock_get.return_value.__aenter__.return_value = mock_response

    with patch.object(ClientSession, "get", mock_get):
        result = await client.fetch_image("cat")

    assert result == ImageResult("https://cataas.com/cat/mockid", "https://cataas.com")
    mock_get.assert_called_once()

    # Test absolute url
    mock_response.json = AsyncMock(return_value={"url": "https://example.com/cat.jpg"})
    with patch.object(ClientSession, "get", mock_get):
        result = await client.fetch_image("cat")

    assert result == ImageResult("https://example.com/cat.jpg", "https://cataas.com")


async def test_fetch_duck(client: AnimalClient) -> None:
    # Duck API just returns a formatted URL without HTTP requests in the client
    with patch("time.time", return_value=12345.0):
        result = await client.fetch_image("duck")

    assert result == ImageResult(
        "https://random-d.uk/api/randomimg?t=12345000", "https://random-d.uk"
    )


async def test_fetch_fox(client: AnimalClient) -> None:
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={"image": "https://randomfox.ca/images/123.jpg", "link": "..."}
    )
    mock_response.raise_for_status = MagicMock()

    mock_get = MagicMock()
    mock_get.return_value.__aenter__.return_value = mock_response

    with patch.object(ClientSession, "get", mock_get):
        result = await client.fetch_image("fox")

    assert result == ImageResult(
        "https://randomfox.ca/images/123.jpg", "https://randomfox.ca/floof/"
    )
    mock_get.assert_called_once()


async def test_fetch_unknown(client: AnimalClient) -> None:
    with patch.object(client, "_fetch_animality", AsyncMock(return_value=None)):
        result = await client.fetch_image("unknown_animal")
    assert result is None


async def test_fetch_animality_success(client: AnimalClient) -> None:
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"image": "https://cdn.animality.xyz/panda/1.png"})
    mock_response.raise_for_status = MagicMock()

    mock_get = MagicMock()
    mock_get.return_value.__aenter__.return_value = mock_response

    with patch.object(ClientSession, "get", mock_get):
        result = await client.fetch_image("panda")

    assert result == ImageResult("https://cdn.animality.xyz/panda/1.png", "https://animality.xyz")


async def test_fetch_animality_error(client: AnimalClient) -> None:
    mock_get = MagicMock()
    mock_get.return_value.__aenter__.side_effect = Exception("Animality Error")

    with patch.object(ClientSession, "get", mock_get):
        result = await client.fetch_image("panda")

    assert result is None


async def test_fetch_error(client: AnimalClient) -> None:
    mock_get = MagicMock()
    mock_get.return_value.__aenter__.side_effect = Exception("API Error")

    with patch.object(ClientSession, "get", mock_get):
        result = await client.fetch_image("dog")

    assert result is None
