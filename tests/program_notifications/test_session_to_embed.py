from datetime import datetime, timezone

import pytest

from program_notifications import session_to_embed
from program_notifications.models import Session, Speaker
from program_notifications.session_to_embed import (
    _AUTHOR_WIDTH,
    _FIELD_VALUE_EMPTY,
    _TITLE_WIDTH,
    _TWEET_WIDTH,
    LevelColors,
)

_QUESTION_PUBLIC_PROFILE = 3656
_QUESTION_LEVEL_ID = 3662


@pytest.fixture
def session() -> Session:
    """Create a dummy session object."""
    return Session(
        id=12345,
        duration="01:00",
        type="session",
        room="Forum Hall",
        slug="example-session",
        persons=[
            Speaker(
                code="BBBBBB",
                public_name="Jane Doe",
                avatar="",
                answers=[
                    {"question": _QUESTION_PUBLIC_PROFILE, "answer": "https://example.com/speaker"}
                ],
            ),
            Speaker(
                code="CCCCCC",
                public_name="John Doe",
                avatar="",
                answers=[
                    {"question": _QUESTION_PUBLIC_PROFILE, "answer": "https://example.com/speaker2"}
                ],
            ),
        ],
        date="2024-07-10T08:00:00+00:00",
        title="Example Session",
        track=None,
        abstract="",
        url="https://example.com/session",
        answers=[
            {
                "question": _QUESTION_LEVEL_ID,
                "answer": "basic",
                "options": [
                    {"en": "Basic (0-2 years)"},
                ],
            },
        ],
    )


def test_embed_title_short(session: Session) -> None:
    """Test the title of the embed with a short title."""
    session.title = "Short Session Title"
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.title == "Short Session Title"


def test_embed_title_long(session: Session) -> None:
    """Test the title of the embed with a long title."""
    session.title = (
        "This is a long title which exceeds our maximum embed title length, "
        "so we expect it to be shortened by our session-to-embed converter. "
    )
    assert len(session.title) > _TITLE_WIDTH

    embed = session_to_embed.create_session_embed(session, None)
    assert embed.title == (
        "This is a long title which exceeds our maximum embed title length, "
        "so we expect it to be shortened by our session-to-embed [...]"
    )


def test_embed_description_short(session: Session) -> None:
    """Test the description (tweet) of the embed with a short description."""
    session.abstract = "Short tweet."
    embed = session_to_embed.create_session_embed(session, None)
    assert (
        embed.description == f"Short tweet.\n\n[Lee más información de esta sesión]({session.url})"
    )


def test_embed_description_long(session: Session) -> None:
    """Test the description (tweet) of the embed with a long description."""
    session.abstract = (
        "This is a long tweet which exceeds our maximum embed description length, "
        "so we expect it to be shortened by our session-to-embed converter. Adding "
        "more text to make sure it exceeds the limit. And even more text. And more. "
    )
    assert len(session.abstract) > _TWEET_WIDTH

    embed = session_to_embed.create_session_embed(session, None)
    assert embed.description == (
        "This is a long tweet which exceeds our maximum embed description length, "
        "so we expect it to be shortened by our session-to-embed converter. Adding "
        "more text to make sure it exceeds the limit. [...]"
        f"\n\n[Lee más información de esta sesión]({session.url})"
    )


def test_embed_description_empty(session: Session) -> None:
    """Test the description (tweet) of the embed when tweet is empty."""
    session.abstract = ""
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.description is None


def test_embed_url(session: Session) -> None:
    """Test the URL of the embed."""
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.url == "https://example.com/session"


@pytest.mark.parametrize(
    "level,expected_color",
    [
        ("basic", LevelColors.BASIC.value),
        ("intermediate", LevelColors.INTERMEDIATE.value),
        ("advanced", LevelColors.ADVANCED.value),
    ],
)
def test_embed_color(session: Session, level: str, expected_color: int) -> None:
    """Test the color of the embed based on session level."""
    session.level = level
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.color.value == expected_color


def test_embed_fields_start_time(session: Session) -> None:
    """Test the 'Start Time' field of the embed."""
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[0].name == "Start Time"
    assert embed.fields[0].value.startswith("<t:")
    assert embed.fields[0].value.endswith(":f>")


def test_embed_fields_room(session: Session) -> None:
    """Test the 'Room' field of the embed."""
    session.room = "Exhibit Hall"
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[1].name == "Room"
    assert embed.fields[1].value == "Exhibit Hall"


def test_embed_fields_track(session: Session) -> None:
    """Test the 'Track' field of the embed."""
    session.track = "Main Track"
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[2].name == "Track"
    assert embed.fields[2].value == "Main Track"


def test_embed_fields_track_empty(session: Session) -> None:
    """Test the 'Track' field of the embed when track is None."""
    session.track = None
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[2].name == "Track"
    assert embed.fields[2].value == _FIELD_VALUE_EMPTY


def test_embed_fields_duration(session: Session) -> None:
    """Test the 'Duration' field of the embed."""
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[3].name == "Duration"
    assert embed.fields[3].value == "60 minutes"


def test_embed_fields_livestream_empty(session: Session) -> None:
    """Test the 'Livestream' field of the embed."""
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[4].name == "Livestream"
    assert embed.fields[4].value == _FIELD_VALUE_EMPTY


def test_embed_fields_livestream_url(session: Session) -> None:
    """Test the 'Livestream' field of the embed."""
    embed = session_to_embed.create_session_embed(session, "https://livestream.url")
    assert embed.fields[4].name == "Livestream"
    assert embed.fields[4].value == "[YouTube](https://livestream.url)"


def test_embed_fields_level(session: Session) -> None:
    """Test the 'Level' field of the embed."""
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[5].name == "Level"
    assert embed.fields[5].value == "Basic"

    session.level = "intermediate"
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[5].value == "Intermediate"

    session.level = "advanced"
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.fields[5].value == "Advanced"


def test_create_author_from_speakers(session: Session) -> None:
    """Test the author creation."""
    session.persons[1].avatar = "https://example.com/avatar2.jpg"
    author = session_to_embed._create_author_from_speakers(session.persons)

    # Should combine the names of all speakers
    assert author["name"] == "Jane Doe, John Doe"

    # Should use the avatar of the first speaker with an avatar
    assert author["icon_url"] == "https://example.com/avatar2.jpg"

    # Should use the website URL of the first speaker
    assert author["website_url"] == "https://example.com/speaker"


def test_create_author_from_speakers_with_no_avatar(session: Session) -> None:
    """Test the author creation with no avatar."""
    session.persons[0].avatar = ""
    session.persons[1].avatar = ""

    author = session_to_embed._create_author_from_speakers(session.persons)
    assert author["icon_url"] is None


def test_create_author_with_long_name(session: Session) -> None:
    """Test the author creation when the speaker has a long name."""
    session.persons[0].name = (
        "This is a very long speaker name which exceeds our maximum author name length, "
        "so we expect it to be shortened by our session-to-embed converter. "
    )
    assert len(session.persons[0].name) > _AUTHOR_WIDTH

    author = session_to_embed._create_author_from_speakers(session.persons)
    assert author["name"] == (
        "This is a very long speaker name which exceeds our maximum author name length, "
        "so we expect it to be shortened by our [...]"
    )


def test_create_author_without_speakers(session: Session) -> None:
    """Test the author creation when session has no speakers."""
    session.persons = []
    author = session_to_embed._create_author_from_speakers(session.persons)
    assert author is None


def test_embed_footer(session: Session) -> None:
    """Test the footer of the embed."""
    embed = session_to_embed.create_session_embed(session, None)
    assert embed.footer.text == "This session starts at 08:00:00 (local conference time)"


def test_format_start_time(session: Session) -> None:
    """Test the _format_start_time function."""
    formatted_start_time = session_to_embed._format_start_time(session.start)
    assert formatted_start_time.startswith("<t:")
    assert formatted_start_time.endswith(":f>")

    # The following code assumes that the start time in the mock data is in UTC.
    datetime_obj = datetime.fromtimestamp(
        int(formatted_start_time.replace("<t:", "").replace(":f>", "")), tz=timezone.utc
    )
    assert datetime_obj == session.start


def test_format_duration(session: Session) -> None:
    """Test the _format_duration function."""
    formatted_duration = session_to_embed._format_duration(session.duration)
    assert formatted_duration == "60 minutes"


def test_format_track(session: Session) -> None:
    """Test the _format_track function."""
    session.track = "Main Track"
    formatted_track = session_to_embed._format_track(session.track)
    assert formatted_track == session.track


def test_format_track_none(session: Session) -> None:
    """Test the _format_track function when track is None."""
    session.track = None
    formatted_track = session_to_embed._format_track(session.track)
    assert formatted_track == _FIELD_VALUE_EMPTY


def test_format_room(session: Session) -> None:
    """Test the _format_room function."""
    formatted_room = session_to_embed._format_room(session.room)
    if session.room:
        assert formatted_room == session.room
    else:
        assert formatted_room == _FIELD_VALUE_EMPTY
