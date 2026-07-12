import logging
from typing import Literal

import aiohttp

from europython_discord.animals.providers.animal_image_provider import AnimalImage
from europython_discord.animals.providers.http_animal_image_provider import HttpAnimalImageProvider

logger = logging.getLogger(__name__)

_SupportedAnimal = Literal[
    "cat",
    "dog",
    "bird",
    "panda",
    "redpanda",
    "koala",
    "fox",
    "whale",
    "dolphin",
    "kangaroo",
    "rabbit",
    "lion",
    "bear",
    "frog",
    "duck",
    "penguin",
    "axolotl",
    "capybara",
    "hedgehog",
    "turtle",
    "narwhal",
    "squirrel",
    "fish",
    "horse",
]


class AnimalityProvider(HttpAnimalImageProvider):
    def __init__(self, animal: _SupportedAnimal) -> None:
        super().__init__()
        self.animal = animal

    def get_url(self) -> str:
        return f"https://api.animality.xyz/img/{self.animal}"

    async def parse_response(self, response: aiohttp.ClientResponse) -> AnimalImage | None:
        response_data = await response.json()
        if "image" not in response_data:
            logger.error("Unexpected response: %s", response_data)
            return None

        return AnimalImage(
            url=response_data["image"],
            source="https://animality.xyz",
        )
