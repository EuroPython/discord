import logging
from urllib.parse import urlencode

import aiohttp

from europython_discord.animals.providers.animal_image_provider import (
    AnimalImage,
)
from europython_discord.animals.providers.http_animal_image_provider import HttpAnimalImageProvider

logger = logging.getLogger(__name__)


class CatAasProvider(HttpAnimalImageProvider):
    def get_url(self) -> str:
        params = {
            "position": "center",
            "font": "Impact",
            "fontSize": "50",
            "fontColor": "#fff",
            "fontBackground": "none",
            "json": "true",
        }
        return "https://cataas.com/cat/says/I%20love%20EuroPython?" + urlencode(params)

    async def parse_response(self, response: aiohttp.ClientResponse) -> AnimalImage | None:
        response_data = await response.json()
        if "url" not in response_data:
            logger.error("Unexpected response: %s", response_data)
            return None

        url = response_data["url"]
        if not url.startswith("http"):
            url = f"https://cataas.com{url}"

        return AnimalImage(
            url=url,
            source="https://cataas.com",
        )
