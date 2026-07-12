from abc import ABC, abstractmethod

import aiohttp

from europython_discord.animals.providers.animal_image_provider import (
    AnimalImage,
    AnimalImageProvider,
    logger,
)


class HttpAnimalImageProvider(AnimalImageProvider, ABC):
    @abstractmethod
    def get_url(self) -> str: ...

    @abstractmethod
    async def parse_response(self, response: aiohttp.ClientResponse) -> AnimalImage | None: ...

    async def generate_image(self) -> AnimalImage | None:
        url = self.get_url()
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url) as response,
            ):
                response.raise_for_status()
        except Exception:  # noqa: BLE001
            logger.exception(f"Failed to fetch animal image from {url}")
            return None

        try:
            return await self.parse_response(response)
        except Exception:  # noqa: BLE001
            logger.exception(f"Failed to parse API response from {url}")
            return None
