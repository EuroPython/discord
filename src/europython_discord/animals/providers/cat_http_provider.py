import random

from europython_discord.animals.providers.animal_image_provider import (
    AnimalImage,
    AnimalImageProvider,
)

_STATUS_CODES: list[int] = [
    *(100, 101, 102, 103, 200, 201, 202, 203, 204, 205, 206, 207, 208),
    *(214, 226, 300, 301, 302, 303, 304, 305, 307, 308, 400, 401, 402),
    *(403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415),
    *(416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 428, 429),
    *(431, 444, 450, 451, 495, 496, 497, 498, 499, 500, 501, 502, 503),
    *(504, 506, 507, 508, 509, 510, 511, 521, 522, 523, 525, 530, 599),
]


class HttpCatProvider(AnimalImageProvider):
    async def generate_image(self) -> AnimalImage:
        status_code = random.choice(_STATUS_CODES)  # noqa: S311 suspicious-non-cryptographic-random-usage
        return AnimalImage(
            url=f"https://http.cat/{status_code}.jpg",
            source="https://http.cat",
        )
