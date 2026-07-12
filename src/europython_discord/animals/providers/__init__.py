from europython_discord.animals.providers.animal_image_provider import AnimalImageProvider
from europython_discord.animals.providers.animality_provider import AnimalityProvider
from europython_discord.animals.providers.cat_http_provider import HttpCatProvider
from europython_discord.animals.providers.cataas_provider import CatAasProvider
from europython_discord.animals.providers.dog_ceo_provider import DogCeoProvider
from europython_discord.animals.providers.random_d_http_provider import RandomDuckHttpProvider
from europython_discord.animals.providers.random_d_provider import RandomDuckProvider
from europython_discord.animals.providers.random_fox_provider import RandomFoxProvider


def get_all_providers() -> dict[str, list[AnimalImageProvider]]:
    return {
        "dog": [DogCeoProvider(), AnimalityProvider("dog")],
        "cat": [CatAasProvider(), HttpCatProvider(), AnimalityProvider("cat")],
        "duck": [RandomDuckProvider(), RandomDuckHttpProvider(), AnimalityProvider("duck")],
        "fox": [RandomFoxProvider(), AnimalityProvider("fox")],
        "bird": [AnimalityProvider("bird")],
        "panda": [AnimalityProvider("panda")],
        "redpanda": [AnimalityProvider("redpanda")],
        "koala": [AnimalityProvider("koala")],
        "whale": [AnimalityProvider("whale")],
        "dolphin": [AnimalityProvider("dolphin")],
        "kangaroo": [AnimalityProvider("kangaroo")],
        "rabbit": [AnimalityProvider("rabbit")],
        "lion": [AnimalityProvider("lion")],
        "bear": [AnimalityProvider("bear")],
        "frog": [AnimalityProvider("frog")],
        "penguin": [AnimalityProvider("penguin")],
        "axolotl": [AnimalityProvider("axolotl")],
        "capybara": [AnimalityProvider("capybara")],
        "hedgehog": [AnimalityProvider("hedgehog")],
        "turtle": [AnimalityProvider("turtle")],
        "narwhal": [AnimalityProvider("narwhal")],
        "squirrel": [AnimalityProvider("squirrel")],
        "fish": [AnimalityProvider("fish")],
        "horse": [AnimalityProvider("horse")],
    }
