from __future__ import annotations

from datetime import date

from pydantic import AwareDatetime, BaseModel


class DaySchedule(BaseModel):
    """Schedule of a single day of EuroPython."""

    rooms: list[str]
    events: list[Session | Break]


class Schedule(BaseModel):
    """Complete schedule of EuroPython."""

    days: dict[date, DaySchedule]


class Break(BaseModel):
    """Break in the EuroPython schedule."""

    event_type: str
    title: str
    duration: int
    rooms: list[str]
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
    rooms: list[str]
    start: AwareDatetime
    website_url: str
    duration: int

    def __hash__(self) -> int:
        return hash(self.code + str(self.start))


class Speaker(BaseModel):
    """Speaker of a Session."""

    code: str
    name: str
    avatar: str
    website_url: str
