from __future__ import annotations

from pydantic import BaseModel


class AnimalsConfig(BaseModel):
    channel_name: str
    cooldown_seconds: int
