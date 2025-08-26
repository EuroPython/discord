"""Models to represent EuroPython sessions."""

from __future__ import annotations

import arrow
import attrs
import yarl
from attrs import validators

_optional_string = validators.optional(validators.instance_of(str))
_optional_int = validators.optional(validators.instance_of(int))
_optional_url = validators.optional(validators.instance_of(yarl.URL))
# _optional_arrow = validators.optional(validators.instance_of(arrow.Arrow))


@attrs.define(frozen=True)
class TranslatedString:
    """A translated string with an `en` field for English."""

    en: str = attrs.field(alias="en", validator=validators.instance_of(str))


_optional_ts = validators.optional(validators.instance_of(TranslatedString))


@attrs.define(frozen=True)
class Speaker:
    """A speaker associated with a session."""

    code: str = attrs.field(validator=validators.instance_of(str))
    name: str | None = attrs.field(validator=_optional_string, default=None)
    avatar_url: str | None = attrs.field(validator=_optional_string, default=None)


_list_of_speakers = validators.deep_iterable(validators.instance_of(Speaker), validators.instance_of(list))


@attrs.define(frozen=True)
class Room:
    """A room associated with a session."""

    id: int = attrs.field(validator=validators.instance_of(int))
    name: TranslatedString | None = attrs.field(validator=_optional_ts, default=None)


_optional_room = validators.optional(validators.instance_of(Room))


# @attrs.define(frozen=True)
# class Slot:
#     """The slot information of a session."""
#     room_id: int = attrs.field(validator=validators.instance_of(int))


@attrs.define()
class Track:
    """A conference session track."""

    id: int = attrs.field(validator=validators.instance_of(int))
    name: TranslatedString | None = attrs.field(validator=_optional_ts, default=None)
    # description: TranslatedString | None = attrs.field(validator=_optional_ts, default=None)


_optional_track = validators.optional(validators.instance_of(Track))


@attrs.define()
class Submission:
    """A conference session submission."""

    code: str = attrs.field(validator=validators.instance_of(str))
    title: str | None = attrs.field(validator=_optional_string, default=None)
    abstract: str | None = attrs.field(validator=_optional_string, default=None)
    speakers: list[Speaker] = attrs.field(validator=_list_of_speakers, default=attrs.Factory(list))
    duration: int | None = attrs.field(validator=_optional_int, default=None)
    track: Track | None = attrs.field(validator=_optional_track, default=None)


_optional_submission = validators.optional(validators.instance_of(Submission))


@attrs.define()
class Session:
    """A conference session."""

    id: int = attrs.field(validator=validators.instance_of(int))
    start: arrow.Arrow = attrs.field(validator=validators.instance_of(arrow.Arrow))
    duration: int | None = attrs.field(validator=_optional_int, default=None)
    description: TranslatedString | None = attrs.field(validator=_optional_ts, default=None)
    room: Room | None = attrs.field(validator=_optional_room, default=None)
    submission: Submission | None = attrs.field(validator=_optional_submission, default=None)

    # speakers: list[Speaker] = attrs.field(validator=_list_of_speakers, default=attrs.Factory(list))
    # title: str | None = attrs.field(validator=_optional_string, default=None)
    # abstract: str | None = attrs.field(validator=_optional_string, default=None)
    # track: TranslatedString | None = attrs.field(validator=_optional_ts, default=None)
    url: yarl.URL | None = attrs.field(validator=_optional_url, default=None)
    experience: str | None = attrs.field(validator=_optional_string, default=None)
    livestream_url: yarl.URL | None = attrs.field(validator=_optional_url, default=None)
    discord_channel_id: str | None = attrs.field(validator=_optional_string, default=None)
    q_and_a_url: yarl.URL | None = attrs.field(validator=_optional_url, default=None)


@attrs.define(frozen=True)
class Break:
    """Represents schedule break information fetched from Pretalx."""

    room: TranslatedString = attrs.field(validator=validators.instance_of(TranslatedString))
    room_id: int = attrs.field(validator=validators.instance_of(int))
    start: arrow.Arrow = attrs.field(validator=validators.instance_of(arrow.Arrow))
    end: arrow.Arrow = attrs.field(validator=validators.instance_of(arrow.Arrow))
    description: TranslatedString = attrs.field(validator=validators.instance_of(TranslatedString))


@attrs.define(frozen=True)
class Schedule:
    """A conference schedule, as fetched from Pretalx."""

    sessions: list[Session] = attrs.field(
        validator=validators.deep_iterable(validators.instance_of(Session), validators.instance_of(list)),
    )
    version: str = attrs.field(validator=validators.instance_of(str))
    schedule_hash: str = attrs.field(validator=validators.matches_re(r"[0-9a-f]{40}"))
    breaks: list[Break] = attrs.field(
        validator=validators.deep_iterable(validators.instance_of(Break), validators.instance_of(list)),
    )
