from __future__ import annotations

from pydantic import BaseModel

ANIMALITY_ANIMALS = [
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


class AnimalSpecificConfig(BaseModel):
    error_messages: list[str]


class AnimalsConfig(BaseModel):
    channel_name: str
    cooldown_seconds: int
    dog: AnimalSpecificConfig
    cat: AnimalSpecificConfig
    duck: AnimalSpecificConfig
    fox: AnimalSpecificConfig
    animality_error_messages: list[str] = [
        "The {plural} are on strike today! Try again later.",
        "A wild error appeared! The {animal} got away...",
        "The {animal} API is fetching a treat. Try again!",
        "404: {plural} not found. Have you checked the nearest zoo?",
    ]
