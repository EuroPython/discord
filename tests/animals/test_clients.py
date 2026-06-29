import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from aiohttp import ClientSession

from europython_discord.animals.clients import AnimalClient


@pytest.fixture
async def client() -> AnimalClient:
    c = AnimalClient()
    yield c
    await c._session.close()


async def test_fetch_dog(client: AnimalClient) -> None:
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"message": "https://images.dog.ceo/dog.jpg", "status": "success"})
    mock_response.raise_for_status = MagicMock()
    
    mock_get = MagicMock()
    mock_get.return_value.__aenter__.return_value = mock_response

    with patch.object(ClientSession, 'get', mock_get):
        url = await client.fetch_image("dog")
        
    assert url == "https://images.dog.ceo/dog.jpg"
    mock_get.assert_called_once()


async def test_fetch_cat(client: AnimalClient) -> None:
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"url": "/cat/mockid"})
    mock_response.raise_for_status = MagicMock()
    
    mock_get = MagicMock()
    mock_get.return_value.__aenter__.return_value = mock_response

    with patch.object(ClientSession, 'get', mock_get):
        url = await client.fetch_image("cat")
        
    assert url == "https://cataas.com/cat/mockid"
    mock_get.assert_called_once()
    
    # Test absolute url
    mock_response.json = AsyncMock(return_value={"url": "https://example.com/cat.jpg"})
    with patch.object(ClientSession, 'get', mock_get):
        url = await client.fetch_image("cat")
        
    assert url == "https://example.com/cat.jpg"


async def test_fetch_duck(client: AnimalClient) -> None:
    # Duck API just returns a formatted URL without HTTP requests in the client
    with patch('time.time', return_value=12345.0):
        url = await client.fetch_image("duck")
        
    assert url == "https://random-d.uk/api/randomimg?t=12345000"


async def test_fetch_fox(client: AnimalClient) -> None:
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"image": "https://randomfox.ca/images/123.jpg", "link": "..."})
    mock_response.raise_for_status = MagicMock()
    
    mock_get = MagicMock()
    mock_get.return_value.__aenter__.return_value = mock_response

    with patch.object(ClientSession, 'get', mock_get):
        url = await client.fetch_image("fox")
        
    assert url == "https://randomfox.ca/images/123.jpg"
    mock_get.assert_called_once()


async def test_fetch_unknown(client: AnimalClient) -> None:
    url = await client.fetch_image("unknown_animal")
    assert url is None


async def test_fetch_error(client: AnimalClient) -> None:
    mock_get = MagicMock()
    mock_get.return_value.__aenter__.side_effect = Exception("API Error")

    with patch.object(ClientSession, 'get', mock_get):
        url = await client.fetch_image("dog")
        
    assert url is None
