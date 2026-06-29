from __future__ import annotations

import logging
import time

import aiohttp

_logger = logging.getLogger(__name__)

# APIs to fetch animals
DOG_API_URL = "https://dog.ceo/api/breeds/image/random"
CAT_API_URL = "https://cataas.com/cat/says/I%20love%20EuroPython"
DUCK_API_URL = "https://random-d.uk/api/randomimg"
FOX_API_URL = "https://randomfox.ca/floof/"


class AnimalClient:
    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()

    async def fetch_image(self, animal: str) -> str | None:
        """Fetch a random image for the given animal."""
        if animal == "dog":
            return await self._fetch_dog()
        if animal == "cat":
            return await self._fetch_cat()
        if animal == "duck":
            return await self._fetch_duck()
        if animal == "fox":
            return await self._fetch_fox()
        _logger.warning(f"Sadly we don't have {animal} pics yet :(")
        return None

    async def _fetch_dog(self) -> str | None:
        try:
            async with self._session.get(DOG_API_URL) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch dog image")
            return None

        return data.get("message")

    async def _fetch_fox(self) -> str | None:
        try:
            async with self._session.get(FOX_API_URL) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch fox image")
            return None

        return data.get("image")

    async def _fetch_duck(self) -> str | None:
        timestamp = int(time.time() * 1000)
        return f"{DUCK_API_URL}?t={timestamp}"

    async def _fetch_cat(self) -> str | None:
        params = {
            "position": "center",
            "font": "Impact",
            "fontSize": "50",
            "fontColor": "#fff",
            "fontBackground": "none",
            "json": "true",
        }
        try:
            async with self._session.get(CAT_API_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch cat image")
            return None

        url = data.get("url")
        if url:
            if url.startswith("http"):
                return url
            return f"https://cataas.com{url}"

        return None
