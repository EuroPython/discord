from __future__ import annotations

import logging

import aiohttp

_logger = logging.getLogger(__name__)

CAT_API_URL = "https://cataas.com/cat/says/I%20love%20EuroPython"


class CatClient:
    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()

    async def fetch_random_cat(self) -> str | None:
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
