"""Models to represent EuroPython sessions."""

import arrow
import attrs
import yarl
from attrs import validators

_optional_string = validators.optional(validators.instance_of(str))
_optional_int = validators.optional(validators.instance_of(int))
_optional_url = validators.optional(validators.instance_of(yarl.URL))
_optional_arrow = validators.optional(validators.instance_of(arrow.Arrow))


@attrs.define(frozen=True)
class Speaker:
    """A speaker associated with a session."""

    code: str = attrs.field(validator=validators.instance_of(str))
    name: str = attrs.field(validator=validators.instance_of(str))
    avatar: str | None = attrs.field(validator=_optional_string, default=None)


_list_of_speakers = validators.deep_iterable(
    validators.instance_of(Speaker), validators.instance_of(list)
)


@attrs.define(frozen=True)
class TranslatedString:
    """A translated string with an `en` field for English."""

    en: str = attrs.field(alias="en", validator=validators.instance_of(str))


_optional_ts = validators.optional(validators.instance_of(TranslatedString))


@attrs.define(frozen=True)
class Slot:
    """The slot information of a session."""

    room_id: int = attrs.field(validator=validators.instance_of(int))
    start: arrow.Arrow = attrs.field(validator=validators.instance_of(arrow.Arrow))
    room: TranslatedString | None = attrs.field(validator=_optional_ts, default=None)


@attrs.define()
class Session:
    """A conference session."""

    code: str = attrs.field(validator=validators.instance_of(str))
    slot: Slot = attrs.field(validator=validators.instance_of(Slot))
    speakers: list[Speaker] = attrs.field(validator=_list_of_speakers, default=attrs.Factory(list))
    title: str | None = attrs.field(validator=_optional_string, default=None)
    duration: int | None = attrs.field(validator=_optional_int, default=None)
    abstract: str | None = attrs.field(validator=_optional_string, default=None)
    track: TranslatedString | None = attrs.field(validator=_optional_ts, default=None)
    url: yarl.URL | None = attrs.field(validator=_optional_url, default=None)
    experience: str | None = attrs.field(validator=_optional_string, default=None)
    livestream_url: yarl.URL | None = attrs.field(validator=_optional_url, default=None)
    discord_channel_id: str | None = attrs.field(validator=_optional_string, default=None)


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
        validator=validators.deep_iterable(
            validators.instance_of(Session), validators.instance_of(list)
        ),
    )
    version: str = attrs.field(validator=validators.instance_of(str))
    schedule_hash: str = attrs.field(validator=validators.matches_re(r"[0-9a-f]{40}"))
    breaks: list[Break] = attrs.field(
        validator=validators.deep_iterable(
            validators.instance_of(Break), validators.instance_of(list)
        ),
    )
