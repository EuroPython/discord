"""Translate EuroPython sessions to Discord embeds."""
import textwrap
from typing import Final

from extensions.programme_notifications.domain import discord, europython

_AUTHOR_WIDTH: Final = 128
_ABSTRACT_WIDTH: Final = 200
_ABSTRACT_EMPTY: Final = "*This session does not have an abstract.*"
_TITLE_WIDTH: Final = 128
_FIELD_VALUE_EMTPY: Final = "—"
_EXPERIENCE_COLORS: Final = {
    "advanced": 13846600,
    "intermediate": 16764229,
    "beginner": 6542417,
}
_EUROPYTHON_WEBSITE: Final = "[europython.eu](https://europython.eu)"


def create_session_embed(
    session: europython.Session,
    include_discord_channel: bool = True,
) -> discord.Embed:
    """Create a Discord embed for a conference session.

    :param session: The session information as provided by Pretalx
    :param include_discord_channel: If the discord channel should be
      linked in the embed
    :return: A Discord embed for this session
    """
    livestream_value = (
        f"[YouTube]({session.livestream_url})" if session.livestream_url else _FIELD_VALUE_EMTPY
    )
    fields = [
        discord.Field(name="Start Time", value=_format_start_time(session), inline=True),
        discord.Field(name="Room", value=_format_room(session), inline=True),
        discord.Field(name="Track", value=_format_track(session), inline=True),
        discord.Field(name="Duration", value=_format_duration(session.duration), inline=True),
        discord.Field(name="Livestream", value=livestream_value, inline=True),
    ]
    if include_discord_channel and session.discord_channel_id:
        channel_value = f"<#{session.discord_channel_id}>"
        fields.append(discord.Field(name="Discord Channel", value=channel_value, inline=True))
    elif session.experience in _EXPERIENCE_COLORS:
        experience = session.experience.capitalize()
        fields.append(discord.Field(name="Level", value=experience, inline=True))
    else:
        fields.append(discord.Field("EuroPython Website", value=_EUROPYTHON_WEBSITE, inline=True))

    return discord.Embed(
        title=_format_title(session.title),
        author=_create_author_from_speakers(session.speakers),
        description=_create_description(session),
        fields=fields,
        footer=_format_footer(session),
        url=str(session.url) if session.url else None,
        color=_get_color(session.experience),
    )


def _create_author_from_speakers(speakers: list[europython.Speaker]) -> discord.Author | None:
    """Create a single embed author from the session speakers.

    If the list contains multiple speakers, the names are combined into
    a single author `name`. The `icon_url` is set to the avatar url of
    the first speaker that has a truthy avatar url; if no truthy avatar
    is observed, `None` is used instead.

    :param speakers: A list of speakers
    :return: An author for a Discord embed
    """
    match speakers:
        case [speaker]:
            author_name = speaker.name
        case [first_speaker, second_speaker]:
            author_name = f"{first_speaker.name} & {second_speaker.name}"
        case [*first_speakers, last_speaker]:
            author_name = ", ".join(s.name for s in first_speakers) + f", & {last_speaker.name}"
        case _:
            return None
    author_name = textwrap.shorten(author_name, width=_AUTHOR_WIDTH)
    icon_url = next((avatar for speaker in speakers if (avatar := speaker.avatar)), None)
    return discord.Author(name=author_name, icon_url=icon_url)


def _create_description(session: europython.Session) -> str:
    """Create an embed description from the session.

    :param session: The session
    :return: The embed description
    """
    url = session.url
    abstract = (
        _ABSTRACT_EMPTY
        if not session.abstract
        else textwrap.shorten(session.abstract, width=_ABSTRACT_WIDTH)
    )
    return f"{abstract}\n\n[Read more about this session]({url})" if url else abstract


def _format_title(title: str | None) -> str | None:
    """Format a session title for a Discord embed.

    :param title: The optional title
    :return: The optional title for an embed
    """
    if not title:
        return None

    return textwrap.shorten(title, width=_TITLE_WIDTH)


def _format_start_time(session: europython.Session) -> str:
    """Format the start time to a Discord timestamp string.

    :param session: The session
    :return: A start time value for the embed. If a start time is
      unavailable, this function returns a placeholder value.
    """
    try:
        start_time_timestamp = session.slot.start.int_timestamp
    except AttributeError:
        return _FIELD_VALUE_EMTPY

    return f"<t:{start_time_timestamp}:f>"


def _format_footer(session: europython.Session) -> discord.Footer | None:
    """Create a footer with the local conference time

    :param session: The session
    :return: A `Footer`, if a start time is available, else `none`
    """
    try:
        formatted_time = session.slot.start.strftime("%H:%M:%S")
    except AttributeError:
        return None

    return discord.Footer(f"This session starts at {formatted_time} (local" f" conference time)")


def _format_room(session: europython.Session) -> str:
    """Format the start time to a Discord timestamp string.

    :param session: The session
    :return: The name of a room or a placeholder value.
    """
    try:
        room = session.slot.room.en
    except AttributeError:
        return _FIELD_VALUE_EMTPY

    return room if room else _FIELD_VALUE_EMTPY


def _format_track(session: europython.Session) -> str:
    """Format the track of a session.

    :param session: The session
    :return: The name of a track or a placeholder value.
    """
    try:
        track = session.track.en
    except AttributeError:
        return _FIELD_VALUE_EMTPY

    return track if track else _FIELD_VALUE_EMTPY


def _format_duration(duration: int | None) -> str:
    """Format the duration of a session.

    :param duration: The duration of a session
    :return: The name of a track or a placeholder value.
    """
    if not duration:
        return _FIELD_VALUE_EMTPY

    return f"{duration} minutes"


def _get_color(experience: str | None) -> int | None:
    """Get the color for the embed based on the audience experience.

    :param experience: The expected audience experience
    :return: A color (int) or None
    """
    try:
        return _EXPERIENCE_COLORS[experience]
    except KeyError:
        return None
