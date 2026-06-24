from __future__ import annotations

import logging

import aiohttp

_logger = logging.getLogger(__name__)

DOG_API_URL = "https://dog.ceo/api/breeds/image/random"


class DogClient:
    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()

    async def fetch_random_dog(self) -> str | None:
        try:
            async with self._session.get(DOG_API_URL) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch dog image")
            return None

        return data["message"]
