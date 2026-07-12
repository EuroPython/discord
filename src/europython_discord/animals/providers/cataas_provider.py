from europython_discord.animals.providers.animal_image_provider import (
    AnimalImage,
    AnimalImageProvider,
)


class CatAasProvider(AnimalImageProvider):
    async def generate_image(self) -> AnimalImage:
        return AnimalImage(
            url="https://cataas.com/cat/says/I%20love%20EuroPython",
            source="https://cataas.com",
        )
