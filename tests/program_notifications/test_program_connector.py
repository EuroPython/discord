from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import aiohttp
import pytest

from program_notifications.program_connector import ProgramConnector

API_URL = "https://programapi24.europython.eu/2024/schedule.json"
TIMEZONE_OFFSET = 2
CACHE_FILE = "test_cache_schedule.json"


@pytest.mark.asyncio
async def test_parse_schedule(tmp_path):
    connector = ProgramConnector(
        api_url=API_URL,
        timezone_offset=TIMEZONE_OFFSET,
        cache_file=tmp_path / CACHE_FILE,
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            schedule = await response.json()
    parsed_schedule = await connector.parse_schedule(schedule)
    assert len(parsed_schedule) > 0


@pytest.mark.asyncio
async def test_fetch_schedule(tmp_path):
    connector = ProgramConnector(
        api_url=API_URL,
        timezone_offset=TIMEZONE_OFFSET,
        cache_file=tmp_path / CACHE_FILE,
    )
    await connector.fetch_schedule()
    assert connector.sessions_by_day is not None


@pytest.mark.asyncio
async def test_get_now(tmp_path):
    simulated_start_time = datetime(
        2024, 7, 10, 9, 0, tzinfo=timezone(timedelta(hours=TIMEZONE_OFFSET))
    )
    connector = ProgramConnector(
        api_url=API_URL,
        timezone_offset=TIMEZONE_OFFSET,
        cache_file=tmp_path / CACHE_FILE,
        time_multiplier=30,
        simulated_start_time=simulated_start_time,
    )
    now = await connector._get_now()
    assert now > simulated_start_time


@pytest.mark.asyncio
async def test_get_sessions_by_date(tmp_path):
    connector = ProgramConnector(
        api_url=API_URL,
        timezone_offset=TIMEZONE_OFFSET,
        cache_file=tmp_path / CACHE_FILE,
    )
    await connector.fetch_schedule()
    test_date = date(2024, 7, 10)  # Use a date from the available schedule
    sessions = await connector.get_sessions_by_date(test_date)
    assert isinstance(sessions, list)
    assert len(sessions) > 0


@pytest.mark.asyncio
async def test_get_upcoming_sessions_for_room(tmp_path):
    connector = ProgramConnector(
        api_url=API_URL,
        timezone_offset=TIMEZONE_OFFSET,
        cache_file=tmp_path / CACHE_FILE,
    )
    await connector.fetch_schedule()

    # Use a known date and time to ensure we get upcoming sessions
    now = datetime(2024, 7, 10, 8, 56, tzinfo=timezone(timedelta(hours=TIMEZONE_OFFSET)))
    with patch.object(connector, "_get_now", return_value=now):
        upcoming_sessions = await connector.get_upcoming_sessions_for_room("Forum Hall")
    assert isinstance(upcoming_sessions, list)
    assert len(upcoming_sessions) > 0


@pytest.mark.asyncio
async def test_get_sessions_by_date_key_error(tmp_path):
    connector = ProgramConnector(
        api_url=API_URL,
        timezone_offset=TIMEZONE_OFFSET,
        cache_file=tmp_path / CACHE_FILE,
    )
    await connector.fetch_schedule()
    test_date = date(2024, 7, 13)  # Use a date not in the available schedule
    sessions = await connector.get_sessions_by_date(test_date)
    assert sessions == []
