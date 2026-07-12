import http
import random

from europython_discord.animals.providers.animal_image_provider import (
    AnimalImage,
    AnimalImageProvider,
)

_STATUS_CODES: list[int] = [
    status_code.value for status_code in http.HTTPStatus.__members__.values()
]


class HttpCatProvider(AnimalImageProvider):
    async def generate_image(self) -> AnimalImage:
        status_code = random.choice(_STATUS_CODES)  # noqa: S311 suspicious-non-cryptographic-random-usage
        return AnimalImage(
            url=f"https://http.cat/{status_code}.jpg",
            source="https://http.cat",
        )
