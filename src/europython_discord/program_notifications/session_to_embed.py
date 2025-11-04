from __future__ import annotations

import textwrap
from datetime import datetime
from enum import Enum
from typing import Final

from discord import Embed
from discord.utils import escape_markdown, format_dt

from europython_discord.program_notifications.models import Session, Speaker

_AUTHOR_WIDTH: Final = 128
_TWEET_WIDTH: Final = 200
_TITLE_WIDTH: Final = 128
_FIELD_VALUE_EMPTY: Final = "—"


class LevelColors(Enum):
    ADVANCED = 0xD34847
    INTERMEDIATE = 0xFFCD45
    BEGINNER = 0x63D452


def create_session_embed(session: Session, livestream_url: str | None) -> Embed:
    """Create a Discord embed for a conference session.

    :param session: The session information as provided by Pretalx
    :return: A Discord embed for this session
    """
    embed = Embed(
        title=_format_title(escape_markdown(session.title)),
        description=_create_description(session),
        url=session.website_url,
        color=_get_color(session.level),
    )

    embed.add_field(name="Start Time", value=format_dt(session.start), inline=True)
    embed.add_field(name="Room", value=_format_room(session.rooms), inline=True)
    embed.add_field(name="Track", value=_format_track(session.track), inline=True)
    embed.add_field(name="Duration", value=_format_duration(session.duration), inline=True)
    #embed.add_field(name="Livestream", value=_format_live_stream(livestream_url), inline=True)
    embed.add_field(name="Livestream", value=_format_live_stream(session.youtube_url), inline=True)  # Add PyLadiesCon
    embed.add_field(name="Level", value=session.level.capitalize(), inline=True)

    author = _create_author_from_speakers(session.speakers)
    if author:
        embed.set_author(
            name=author["name"], icon_url=author.get("icon_url"), url=author.get("website_url")
        )

    embed.set_footer(text=_format_footer(session.start))

    return embed


def _create_author_from_speakers(speakers: list[Speaker]) -> dict | None:
    """Create a single embed author from the session speakers.

    :param speakers: A list of speakers
    :return: An author for a Discord embed
    """
    if not speakers:
        return None

    author_name = ", ".join(speaker.name for speaker in speakers)
    author_name = textwrap.shorten(author_name, width=_AUTHOR_WIDTH)
    icon_urls = [speaker.avatar for speaker in speakers if speaker.avatar]
    icon_url = icon_urls[0] if icon_urls else None
    website_url = speakers[0].website_url

    return {"name": author_name, "icon_url": icon_url, "website_url": website_url}


def _create_description(session: Session) -> str | None:
    """Create an embed description from the session.

    :param session: The session
    :return: The embed description
    """
    if not session.tweet:
        return None
    tweet_short = textwrap.shorten(escape_markdown(session.tweet), width=_TWEET_WIDTH)
    return f"{tweet_short}\n\n[Read more about this session]({session.website_url})"


def _format_title(title: str) -> str:
    """Format a session title for a Discord embed.

    :param title: The title
    :return: The title for an embed
    """
    return textwrap.shorten(title, width=_TITLE_WIDTH)


def _format_footer(start_time: datetime) -> str:
    """Create a footer with the local conference time.

    :param start_time: The start time
    :return: A footer text
    """
    formatted_time = start_time.strftime("%H:%M:%S")
    return f"This session starts at {formatted_time} (local conference time)"


def _format_room(rooms: list[str]) -> str:
    """Format the room names for a Discord embed.

    :param rooms: The list of rooms
    :return: The name of a room or a placeholder value.
    """
    room = ", ".join(rooms)
    return room if room else _FIELD_VALUE_EMPTY


def _format_track(track: str | None) -> str:
    """Format the track of a session.

    :param track: The track name
    :return: The name of a track or a placeholder value.
    """
    return track or _FIELD_VALUE_EMPTY


def _format_duration(duration: int) -> str:
    """Format the duration of a session.

    :param duration: The duration of a session
    :return: The duration in minutes
    """
    return f"{duration} minutes"


def _format_live_stream(livestream_url: str) -> str:
    """Format the livestream URL for the embed.

    :param livestream_url: The URL of the livestream
    :return: A formatted string for the livestream URL
    """
    return f"[YouTube]({livestream_url})" if livestream_url else _FIELD_VALUE_EMPTY


def _get_color(level: str) -> int:
    """Get the color for the embed based on the audience level.

    :param level: The expected audience level
    :return: A color (int)
    """
    return LevelColors[level.upper()].value
