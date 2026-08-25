from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, Field, computed_field


class DaySchedule(BaseModel):
    """Schedule of a single day of EuroPython."""

    rooms: Annotated[list[str], Field(min_length=1)]
    events: list[Session | Break]


class Schedule(BaseModel):
    """Complete schedule of EuroPython."""

    days: dict[date, DaySchedule]


class Break(BaseModel):
    """Break in the EuroPython schedule."""

    event_type: str
    title: str
    duration: int
    rooms: Annotated[list[str], Field(min_length=1)]
    start: AwareDatetime


class Session(BaseModel):
    """Session in the EuroPython schedule."""

    event_type: str
    code: str
    slug: str
    title: str
    session_type: str
    speakers: list[Speaker]
    tweet: str
    level: str
    track: str | None
    rooms: Annotated[list[str], Field(min_length=1)]
    start: AwareDatetime
    website_url: str
    duration: int

    @property
    @computed_field
    def room(self) -> str:
        return self.rooms[0]

    @property
    @computed_field
    def is_break(self) -> bool:
        return len(self.rooms) > 1


class Speaker(BaseModel):
    """Speaker of a Session."""

    code: str
    name: str
    avatar: str
    website_url: str
