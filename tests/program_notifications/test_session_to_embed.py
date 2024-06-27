from datetime import datetime

from discord import Embed

from program_notifications.models import Session, Speaker
from program_notifications.session_to_embed import create_session_embed


def test_create_session_embed_single_speaker():
    speaker = Speaker(code="a1b2c3", name="John Doe", avatar="", website_url="http://example.com")
    session = Session(
        event_type="session",
        code="xyzabc",
        slug="session-1",
        title="Session 1",
        session_type="talk",
        speakers=[speaker],
        tweet="",
        level="beginner",
        track=None,
        rooms=["Room 1"],
        start=datetime(2023, 6, 27, 10, 0),
        website_url="http://example.com/session-1",
        duration=30,
    )
    embed = create_session_embed(session)
    assert isinstance(embed, Embed)
    assert embed.title == "Session 1"
    assert embed.url == "http://example.com/session-1"
    assert embed.fields[0].name == "Start Time"
    assert embed.fields[1].name == "Room"
    assert embed.fields[2].name == "Track"
    assert embed.fields[3].name == "Duration"
    assert embed.color.value == 6542417
    assert embed.description is None


def test_create_session_embed_multiple_speaker():
    speaker = Speaker(
        code="a1b2c3", name="John Doe", avatar="", website_url="http://Coreexample.com"
    )
    speaker2 = Speaker(code="d4e5f6", name="Jane Doe", avatar="", website_url="http://example2.com")
    session = Session(
        event_type="session",
        code="asdasd",
        slug="session-2",
        title="Session 2",
        session_type="talk",
        speakers=[speaker],
        tweet="Excited for this session!",
        level="advanced",
        track="CPython Core",
        rooms=["Room 1"],
        start=datetime(2023, 6, 27, 10, 0),
        website_url="http://example.com/session-2",
        duration=60,
    )
    embed = create_session_embed(session)
    assert isinstance(embed, Embed)
    assert embed.title == "Session 2"
    assert embed.url == "http://example.com/session-2"
    assert embed.fields[0].value == "<t:1687852800:f>"
    assert embed.fields[1].value == "Room 1"
    assert embed.fields[2].value == "CPython Core"
    assert embed.fields[3].value == "60 minutes"
    assert embed.color.value == 13846600
    assert (
        embed.description
        == "Excited for this session!\n\n[Read more about this session](http://example.com/session-2)"
    )
