from __future__ import annotations

import logging

import aiohttp

_logger = logging.getLogger(__name__)

FOX_API_URL = "https://randomfox.ca/floof/"


class FoxClient:
    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()

    async def fetch_random_fox(self) -> str | None:
        try:
            async with self._session.get(FOX_API_URL) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception:
            _logger.exception("Failed to fetch fox image")
            return None

        return data.get("image")
