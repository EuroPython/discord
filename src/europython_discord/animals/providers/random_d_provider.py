import logging

import aiohttp

from europython_discord.animals.providers.animal_image_provider import AnimalImage
from europython_discord.animals.providers.http_animal_image_provider import HttpAnimalImageProvider

logger = logging.getLogger(__name__)


class RandomDuckProvider(HttpAnimalImageProvider):
    def get_url(self) -> str:
        return "https://random-d.uk/api/v2/quack"

    async def parse_response(self, response: aiohttp.ClientResponse) -> AnimalImage | None:
        response_data = await response.json()
        if "url" not in response_data:
            logger.error("Unexpected response: %s", response_data)
            return None

        return AnimalImage(
            url=response_data["url"],
            source="https://random-d.uk",
        )
