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

    change = ScheduleChange(
        old_session=old_session,
        new_session=new_session,
    )

    cog.programme_connector.fetch_schedule.return_value = [change]

    await cog.fetch_schedule.coro(cog)

    assert "Found 1 schedule changes." in caplog.text

    channel.send.assert_called_once()


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

    assert "Schedule update: Old Title" in message
    assert "Room changed: ['S1'] → ['S2']" in message
    assert "Duration changed: 30 → 45 minutes" in message