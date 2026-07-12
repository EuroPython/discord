from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import aiohttp

_logger = logging.getLogger(__name__)


@dataclass
class ImageResult:
    url: str
    source: str


# APIs to fetch animals
DOG_API_URL = "https://dog.ceo/api/breeds/image/random"
DOG_SOURCE = "https://dog.ceo"
CAT_API_URL = "https://cataas.com/cat/says/I%20love%20EuroPython"
CAT_SOURCE = "https://cataas.com"
DUCK_API_URL = "https://random-d.uk/api/randomimg"
DUCK_SOURCE = "https://random-d.uk"
FOX_API_URL = "https://randomfox.ca/floof/"
FOX_SOURCE = "https://randomfox.ca/floof/"
ANIMALITY_API_URL = "https://api.animality.xyz/img"
ANIMALITY_SOURCE = "https://animality.xyz"


class AnimalClient:
    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()

    async def fetch_image(self, animal: str) -> ImageResult | None:
        """Fetch a random image for the given animal."""
        if animal == "dog":
            return await self._fetch_dog() or await self._fetch_animality(animal)
        if animal == "cat":
            return await self._fetch_cat() or await self._fetch_animality(animal)
        if animal == "duck":
            return await self._fetch_duck() or await self._fetch_animality(animal)
        if animal == "fox":
            return await self._fetch_fox() or await self._fetch_animality(animal)

        return await self._fetch_animality(animal)

    async def _fetch_dog(self) -> ImageResult | None:
        try:
            async with self._session.get(DOG_API_URL) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch dog image")
            return None

        url = data.get("message")
        return ImageResult(url, DOG_SOURCE) if url else None

    async def _fetch_fox(self) -> ImageResult | None:
        try:
            async with self._session.get(FOX_API_URL) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch fox image")
            return None

        url = data.get("image")
        return ImageResult(url, FOX_SOURCE) if url else None

    async def _fetch_duck(self) -> ImageResult | None:
        timestamp = int(time.time() * 1000)
        return ImageResult(f"{DUCK_API_URL}?t={timestamp}", DUCK_SOURCE)

    async def _fetch_cat(self) -> ImageResult | None:
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
                return ImageResult(url, CAT_SOURCE)
            return ImageResult(f"https://cataas.com{url}", CAT_SOURCE)

        return None

    async def _fetch_animality(self, animal: str) -> ImageResult | None:
        try:
            async with self._session.get(f"{ANIMALITY_API_URL}/{animal}") as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch animality image for %s", animal)
            return None

        url = data.get("image")
        return ImageResult(url, ANIMALITY_SOURCE) if url else None
