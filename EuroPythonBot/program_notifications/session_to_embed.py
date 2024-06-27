import textwrap
from typing import Final

from discord import Embed

from program_notifications.models import Session, Speaker

_AUTHOR_WIDTH: Final = 128
_TWEET_WIDTH: Final = 200
_TITLE_WIDTH: Final = 128
_FIELD_VALUE_EMPTY: Final = "—"
_LEVEL_COLORS: Final = {
    "advanced": 13846600,
    "intermediate": 16764229,
    "beginner": 6542417,
}


def create_session_embed(session: Session) -> Embed:
    """Create a Discord embed for a conference session.

    :param session: The session information as provided by Pretalx
    :return: A Discord embed for this session
    """
    fields = [
        {"name": "Start Time", "value": _format_start_time(session), "inline": True},
        {"name": "Room", "value": _format_room(session), "inline": True},
        {"name": "Track", "value": _format_track(session), "inline": True},
        {"name": "Duration", "value": _format_duration(session.duration), "inline": True},
    ]

    if session.level in _LEVEL_COLORS:
        experience = session.level.capitalize()
        fields.append({"name": "Level", "value": experience, "inline": True})

    embed = Embed(
        title=_format_title(session.title),
        description=_create_description(session) if session.tweet else None,
        url=str(session.website_url) if session.website_url else None,
        color=_get_color(session.level),
    )

    author = _create_author_from_speakers(session.speakers)
    if author:
        embed.set_author(
            name=author["name"], icon_url=author.get("icon_url"), url=author.get("website_url")
        )

    for field in fields:
        embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])

    footer = _format_footer(session)
    if footer:
        embed.set_footer(text=footer)

    return embed


def _create_author_from_speakers(speakers: list[Speaker]) -> dict | None:
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
    website_url = next(
        (website_url for speaker in speakers if (website_url := speaker.website_url)), None
    )
    return {"name": author_name, "icon_url": icon_url, "website_url": website_url}


def _create_description(session: Session) -> str | None:
    """Create an embed description from the session.

    :param session: The session
    :return: The embed description
    """
    url = session.website_url
    tweet = textwrap.shorten(session.tweet, width=_TWEET_WIDTH)
    return f"{tweet}\n\n[Read more about this session]({url})" if url else tweet


def _format_title(title: str | None) -> str | None:
    """Format a session title for a Discord embed.

    :param title: The optional title
    :return: The optional title for an embed
    """
    if not title:
        return None
    return textwrap.shorten(title, width=_TITLE_WIDTH)


def _format_start_time(session: Session) -> str:
    """Format the start time to a Discord timestamp string.

    :param session: The session
    :return: A start time value for the embed. If a start time is
      unavailable, this function returns a placeholder value.
    """
    try:
        start_time_timestamp = int(session.start.timestamp())
    except AttributeError:
        return _FIELD_VALUE_EMPTY
    return f"<t:{start_time_timestamp}:f>"


def _format_footer(session: Session) -> str | None:
    """Create a footer with the local conference time.

    :param session: The session
    :return: A footer text, if a start time is available, else `None`
    """
    try:
        formatted_time = session.start.strftime("%H:%M:%S")
    except AttributeError:
        return None
    return f"This session starts at {formatted_time} (local conference time)"


def _format_room(session: Session) -> str:
    """Format the room names for a Discord embed.

    :param session: The session
    :return: The name of a room or a placeholder value.
    """
    try:
        room = ", ".join(room for room in session.rooms)
    except AttributeError:
        return _FIELD_VALUE_EMPTY
    return room if room else _FIELD_VALUE_EMPTY


def _format_track(session: Session) -> str:
    """Format the track of a session.

    :param session: The session
    :return: The name of a track or a placeholder value.
    """
    try:
        track = session.track
    except AttributeError:
        return _FIELD_VALUE_EMPTY
    return track if track else _FIELD_VALUE_EMPTY


def _format_duration(duration: int | None) -> str:
    """Format the duration of a session.

    :param duration: The duration of a session
    :return: The duration in minutes or a placeholder value.
    """
    if not duration:
        return _FIELD_VALUE_EMPTY
    return f"{duration} minutes"


def _get_color(level: str | None) -> int | None:
    """Get the color for the embed based on the audience level.

    :param level: The expected audience level
    :return: A color (int) or None
    """
    try:
        return _LEVEL_COLORS[level]
    except KeyError:
        return None
