import json
from datetime import datetime
from pathlib import Path

import pytest

from program_notifications import session_to_embed
from program_notifications.models import Session, Speaker

mock_schedule_file = Path(__file__).parent / "mock_schedule.json"


@pytest.fixture
def mock_schedule():
    """Fixture to load the mock schedule data."""
    with mock_schedule_file.open() as f:
        return json.load(f)


def create_session_from_event(event):
    """Helper function to create a Session object from event data."""
    speakers = [Speaker(**speaker_data) for speaker_data in event.get("speakers", [])]
    return Session(
        code=event.get("code"),
        duration=event.get("duration"),
        event_type=event.get("event_type"),
        level=event.get("level"),
        rooms=event.get("rooms", []),
        session_type=event.get("session_type"),
        slug=event.get("slug"),
        speakers=speakers,
        start=event.get("start"),
        title=event.get("title"),
        track=event.get("track"),
        tweet=event.get("tweet", ""),
        website_url=event.get("website_url"),
    )


@pytest.fixture
def sessions(mock_schedule):
    """Fixture to create a list of Session objects from mock data."""
    sessions = []
    for day, day_data in mock_schedule["days"].items():
        for event in day_data["events"]:
            if event["event_type"] == "session":
                sessions.append(create_session_from_event(event))
    return sessions


@pytest.fixture
def embeds(sessions):
    """Fixture to create a list of embeds from the sessions."""
    return [session_to_embed.create_session_embed(session) for session in sessions]


def test_embed_title(sessions, embeds):
    """Test the title of the embed."""
    for session, embed in zip(sessions, embeds):
        assert embed.title == session_to_embed._format_title(session.title)


def test_embed_description(sessions, embeds):
    """Test the description of the embed."""
    for session, embed in zip(sessions, embeds):
        assert embed.description == session_to_embed._create_description(session)


def test_embed_url(sessions, embeds):
    """Test the URL of the embed."""
    for session, embed in zip(sessions, embeds):
        assert embed.url == session.website_url


def test_embed_color(sessions, embeds):
    """Test the color of the embed."""
    for session, embed in zip(sessions, embeds):
        assert embed.color.value == session_to_embed._get_color(session.level)


def test_embed_fields(sessions, embeds):
    """Test the fields of the embed."""
    for session, embed in zip(sessions, embeds):
        fields = embed.fields
        assert fields[0].name == "Start Time"
        assert fields[0].value == session_to_embed._format_start_time(session.start)

        assert fields[1].name == "Room"
        assert fields[1].value == session_to_embed._format_room(session.rooms)

        assert fields[2].name == "Track"
        assert fields[2].value == session_to_embed._format_track(session.track)

        assert fields[3].name == "Duration"
        assert fields[3].value == session_to_embed._format_duration(session.duration)

        assert fields[4].name == "Level"
        assert fields[4].value == session.level.capitalize()


def test_embed_author(sessions, embeds):
    """Test the author of the embed."""
    for session, embed in zip(sessions, embeds):
        if session.speakers:
            author = session_to_embed._create_author_from_speakers(session.speakers)
            assert embed.author.name == author["name"]
            assert embed.author.icon_url == author["icon_url"]
            assert embed.author.url == author["website_url"]
        else:
            assert embed.author.name is None


def test_embed_footer(sessions, embeds):
    """Test the footer of the embed."""
    for session, embed in zip(sessions, embeds):
        footer_text = session_to_embed._format_footer(session.start)
        if footer_text:
            assert embed.footer.text == footer_text
        else:
            assert embed.footer.text is None


def test_format_title(sessions):
    """Test the _format_title function."""
    for session in sessions:
        formatted_title = session_to_embed._format_title(session.title)
        assert len(formatted_title) <= 128


def test_format_start_time(sessions):
    """Test the _format_start_time function."""
    for session in sessions:
        formatted_start_time = session_to_embed._format_start_time(session.start)
        assert formatted_start_time.startswith("<t:")
        assert formatted_start_time.endswith(":f>")


def test_format_duration(sessions):
    """Test the _format_duration function."""
    for session in sessions:
        formatted_duration = session_to_embed._format_duration(session.duration)
        assert formatted_duration.endswith(" minutes")


def test_format_track(sessions):
    """Test the _format_track function."""
    for session in sessions:
        formatted_track = session_to_embed._format_track(session.track)
        if session.track:
            assert formatted_track == session.track
        else:
            assert formatted_track == "—"


def test_format_room(sessions):
    """Test the _format_room function."""
    for session in sessions:
        formatted_room = session_to_embed._format_room(session.rooms)
        if session.rooms:
            assert formatted_room == ", ".join(session.rooms)
        else:
            assert formatted_room == "—"


def test_get_color(sessions):
    """Test the _get_color function."""
    for session in sessions:
        color = session_to_embed._get_color(session.level)
        assert color in [color.value for color in session_to_embed.LevelColors]
