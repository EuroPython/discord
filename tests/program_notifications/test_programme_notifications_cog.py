from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from discord import channel
import pytest

from europython_discord.programme_notifications.cog import (
    ProgrammeNotificationsCog,
    _format_schedule_change,
)
from europython_discord.programme_notifications.models import (
    ScheduleChange,
    Session,
)


@pytest.mark.asyncio
async def test_fetch_schedule_detects_changes(caplog):
    caplog.set_level("INFO")

    cog = object.__new__(ProgrammeNotificationsCog)

    cog.programme_connector = AsyncMock()

    cog.bot = SimpleNamespace()

    cog.config = SimpleNamespace(
    schedule_updates_channel_name="schedule-updates"
)

    channel = AsyncMock()
    channel.name = "schedule-updates"

    cog.bot.get_all_channels = lambda: [channel]

    old_session = Session(
        event_type="session",
        code="ABC123",
        slug="test-session",
        title="Old Title",
        session_type="talk",
        speakers=[],
        tweet="",
        level="beginner",
        track=None,
        rooms=["S1"],
        start=datetime.now(tz=UTC),
        website_url="",
        duration=30,
    )

    new_session = old_session.model_copy(
        update={"title": "New Title"}
    )

    old_schedule = {
       old_session.start.date(): [old_session]
   }
    new_schedule = {
       new_session.start.date(): [new_session]
    }

    cog.programme_connector.sessions_by_day = old_schedule
    cog.programme_connector.fetch_schedule.return_value = new_schedule

    await cog.fetch_schedule.coro(cog)

    assert "Found 1 schedule changes." in caplog.text

    channel.send.assert_called_once()
    assert (
    "Session title changed: Old Title -> New Title"
    in channel.send.call_args.kwargs["content"]
)


def test_format_schedule_change():
    old_session = Session(
        event_type="session",
        code="ABC123",
        slug="test-session",
        title="Old Title",
        session_type="talk",
        speakers=[],
        tweet="",
        level="beginner",
        track=None,
        rooms=["S1"],
        start=datetime(2026, 7, 28, 10, 0, tzinfo=UTC),
        website_url="",
        duration=30,
    )

    new_session = old_session.model_copy(
        update={
            "rooms": ["S2"],
            "duration": 45,
        }
    )

    change = ScheduleChange(
        old_session=old_session,
        new_session=new_session,
    )

    message = _format_schedule_change(change)

    assert "Session: Old Title" in message
    assert "Speakers: " in message
    assert "Time: 28 July 10:00 - 28 July 10:45" in message
    assert "Room: S2" in message
    assert "Room changed: S1 -> S2" in message
    assert (
          "Time changed: 28 July 10:00 - 28 July 10:30 -> "
          "28 July 10:00 - 28 July 10:45"
    ) in message


def test_format_new_session():
    new_session = Session(
        event_type="session",
        code="NEW123",
        slug="new-session",
        title="New Session",
        session_type="talk",
        speakers=[],
        tweet="",
        level="beginner",
        track=None,
        rooms=["S1"],
        start=datetime(2026, 7, 28, 10, 0, tzinfo=UTC),
        website_url="",
        duration=45,
    )

    change = ScheduleChange(
        old_session=None,
        new_session=new_session,
    )

    message = _format_schedule_change(change)

    assert "New Session added: New Session" in message
    assert "Speakers: " in message
    assert "New Room: S1" in message
    assert "Time: 28 July 10:00 - 28 July 10:45" in message

def test_format_cancelled_session():
    old_session = Session(
        event_type="session",
        code="OLD123",
        slug="old-session",
        title="Cancelled Session",
        session_type="talk",
        speakers=[],
        tweet="",
        level="beginner",
        track=None,
        rooms=["S2"],
        start=datetime(2026, 7, 28, 11, 0, tzinfo=UTC),
        website_url="",
        duration=30,
    )

    change = ScheduleChange(
        old_session=old_session,
        new_session=None,
    )

    message = _format_schedule_change(change)

    assert "Session cancelled: Cancelled Session" in message
    assert "Speakers: " in message
    assert "Room: S2" in message
    assert "Time: 28 July 11:00 - 28 July 11:30" in message