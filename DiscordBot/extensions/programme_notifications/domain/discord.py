"""Models to represent Discord objects."""
from typing import Final

import attrs
from attrs import validators

# Discord limits that cannot be exceeded
_MAX_LEN: Final = {
    "author_name": 256,
    "content": 2000,
    "description": 2000,
    "embeds": 10,
    "field_name": 256,
    "field_value": 1024,
    "fields": 25,
    "footer": 2048,
    "title": 256,
}


@attrs.define(frozen=True)
class Field:
    """An embed field."""

    name: str = attrs.field(validator=validators.max_len(_MAX_LEN["field_name"]))
    value: str = attrs.field(validator=validators.max_len(_MAX_LEN["field_value"]))
    inline: bool


@attrs.define(frozen=True)
class Footer:
    """The footer of a Discord embed."""

    text: str = attrs.field(validator=validators.max_len(_MAX_LEN["footer"]))


@attrs.define(frozen=True)
class Author:
    """The author of a Discord embed."""

    name: str = attrs.field(validator=validators.max_len(_MAX_LEN["author_name"]))
    icon_url: str | None = None


@attrs.define(frozen=True)
class Embed:
    """A Discord embed."""

    title: str | None = attrs.field(
        validator=validators.optional(validators.max_len(_MAX_LEN["title"]))
    )
    author: Author | None
    description: str | None = attrs.field(
        validator=validators.optional(validators.max_len(_MAX_LEN["description"]))
    )
    fields: list[Field] | None = attrs.field(
        validator=validators.optional(validators.max_len(_MAX_LEN["fields"]))
    )
    footer: Footer | None
    url: str | None
    color: int | None = attrs.field(
        default=None, validator=validators.optional(validators.instance_of(int))
    )


@attrs.define(frozen=True)
class WebhookMessage:
    """A message to send to a Discord webhook."""

    content: str | None = attrs.field(
        validator=validators.optional(validators.max_len(_MAX_LEN["content"]))
    )
    embeds: list[Embed] = attrs.field(
        default=attrs.Factory(list), validator=validators.max_len(_MAX_LEN["embeds"])
    )
    allowed_mentions: dict[str, list[str]] = attrs.field(
        init=False, default=attrs.Factory(lambda: {"parse": []})
    )
