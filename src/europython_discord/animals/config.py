from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class AnimalKind(StrEnum):
    CAT = "cat"
    DOG = "dog"
    BIRD = "bird"
    PANDA = "panda"
    REDPANDA = "redpanda"
    KOALA = "koala"
    FOX = "fox"
    WHALE = "whale"
    DOLPHIN = "dolphin"
    KANGAROO = "kangaroo"
    RABBIT = "rabbit"
    LION = "lion"
    BEAR = "bear"
    FROG = "frog"
    DUCK = "duck"
    PENGUIN = "penguin"
    AXOLOTL = "axolotl"
    CAPYBARA = "capybara"
    HEDGEHOG = "hedgehog"
    TURTLE = "turtle"
    NARWHAL = "narwhal"
    SQUIRREL = "squirrel"
    FISH = "fish"
    HORSE = "horse"


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

    @property
    def config_by_kind(self) -> dict[AnimalKind, AnimalSpecificConfig]:
        return {
            AnimalKind.DOG: self.dog,
            AnimalKind.CAT: self.cat,
            AnimalKind.DUCK: self.duck,
            AnimalKind.FOX: self.fox,
        }
