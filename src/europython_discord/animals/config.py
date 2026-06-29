from __future__ import annotations

from pydantic import BaseModel


class AnimalSpecificConfig(BaseModel):
    error_messages: list[str]


class AnimalsConfig(BaseModel):
    channel_name: str
    cooldown_seconds: int
    dog: AnimalSpecificConfig
    cat: AnimalSpecificConfig
    duck: AnimalSpecificConfig
    fox: AnimalSpecificConfig
