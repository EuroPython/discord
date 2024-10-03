from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field

_QUESTION_LEVEL_ID = 3662
_QUESTION_PUBLIC_PROFILE = 3656
_ID_OPENING_TALK = 55677


def level_validator(answers: list[dict[str, Any]]) -> str:
    """Parses the level of the session from the answers

    Args:
        answers (list[dict[str, Any]]): JSON array containing the Pretalx answers.

    Returns:
        :obj:`str`: The level of the session or "NA" if not found
    """
    for answer in answers:
        if answer["question"] == _QUESTION_LEVEL_ID:
            # The answer is a string with the level and a brief description. We only want the level
            # which is the first word in the string. We also convert it to lowercase. We pick the
            # string from the ["options"][0]["en"]
            return answer["options"][0]["en"].split(" ")[0].lower()
    return "NA"


def parse_duration(duration: str) -> int:
    """Parses the duration of a session from a string, returning its total time in minutes.

    Args:
        duration (:obj:`str`): The duration of the session in the format HH:MM

    Returns:
        :obj:`int`: The duration of the session in minutes
    """
    dt = datetime.strptime(duration, "%H:%M")
    return dt.hour * 60 + dt.minute


def public_profile_validator(answers: list[dict[str, Any]]) -> str:
    """Gets the public profile URL of the speaker from the answers

    Args:
        answers (list[dict[str, Any]]): The JSON array containing the Pretalx answers.

    Returns:
        str: The public profile URL of the speaker
    """
    for answer in answers:
        if answer["question"] == _QUESTION_PUBLIC_PROFILE:
            return answer["answer"] or ""
    return ""


class DaySchedule(BaseModel):
    """Schedule of a single day of EuroPython"""

    rooms: dict[str, list[Session]]
    date: date


class Conference(BaseModel):
    """Conference information"""

    title: str
    start: date
    end: date
    days: list[DaySchedule]


class Session(BaseModel):
    """Session in the EuroPython schedule"""

    type: str
    id: int
    slug: str
    title: str
    room: str
    persons: list[Speaker]
    track: str | None
    url: str
    abstract: str
    start: datetime = Field(alias="date")
    level: Annotated[str, BeforeValidator(level_validator)] = Field(alias="answers")
    duration: Annotated[int, BeforeValidator(parse_duration)]

    def __hash__(self) -> int:
        return hash(f"{self.id}{self.start}")

    @property
    def is_break(self) -> bool:
        """Determines if the session is a break"""
        # FIXME: This is a workaround to avoid showing the "Event Opening" as a break
        return (
            self.type.lower()
            in (
                "event opening | accreditations",
                "lunch break",
                "assambly",
                "snack",
                "coffee break",
            )
            and self.id != _ID_OPENING_TALK
        )


class Speaker(BaseModel):
    """Speaker of a Session"""

    code: str
    avatar: str | None
    name: str = Field(alias="public_name")
    website_url: Annotated[str, BeforeValidator(public_profile_validator)] = Field(alias="answers")
