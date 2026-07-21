import asyncio
import json
from datetime import UTC, date, datetime
from http import HTTPStatus
from pathlib import Path

import aiofiles
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from europython_discord.programme_notifications.programme_connector import ProgrammeConnector

mock_schedule_file = Path(__file__).parent / "mock_schedule.json"


@pytest.fixture
def mock_schedule():
    with mock_schedule_file.open() as f:
        return json.load(f)


@pytest.fixture
def cache_file(tmp_path):
    return tmp_path / "cache.json"


@pytest.fixture
async def programme_connector(cache_file):
    return ProgrammeConnector(api_url="http://test.api/schedule", cache_file=cache_file)


@pytest.fixture
async def mock_client(aiohttp_client, unused_tcp_port_factory, mock_schedule):
    async def mock_api_handler(request):  # noqa: ARG001 (unused argument)
        return web.json_response(mock_schedule)

    app = web.Application()
    app.router.add_get("/schedule", mock_api_handler)

    server = TestServer(app, port=unused_tcp_port_factory())
    return await aiohttp_client(server)


@pytest.fixture
async def mock_schedule_url(mock_client):
    return str(mock_client.make_url("/schedule"))


async def test_parse_schedule(programme_connector, mock_schedule):
    sessions_by_day = await programme_connector.parse_schedule(mock_schedule)

    assert len(sessions_by_day) == 3

    assert len(sessions_by_day[date(2024, 7, 10)]) == 4
    assert len(sessions_by_day[date(2024, 7, 11)]) == 3
    assert len(sessions_by_day[date(2024, 7, 12)]) == 3


async def test_fetch_schedule(programme_connector, mock_schedule_url, cache_file, mock_schedule):
    programme_connector._api_url = mock_schedule_url

    await programme_connector.fetch_schedule()

    async with aiofiles.open(cache_file) as f:
        cached_data = json.loads(await f.read())
        assert cached_data == mock_schedule


async def test_get_schedule_from_cache(programme_connector, mock_schedule, cache_file):
    async with aiofiles.open(cache_file, "w") as f:
        await f.write(json.dumps(mock_schedule))

    sessions_by_day = await programme_connector._get_schedule_from_cache()

    assert len(sessions_by_day) == 3
    assert len(sessions_by_day[date(2024, 7, 10)]) == 4
    assert len(sessions_by_day[date(2024, 7, 11)]) == 3
    assert len(sessions_by_day[date(2024, 7, 12)]) == 3


async def test_get_sessions_by_date(programme_connector, mock_schedule_url):
    programme_connector._api_url = mock_schedule_url

    await programme_connector.fetch_schedule()

    # Test for July 10th
    sessions = await programme_connector.get_sessions_by_date(date(2024, 7, 10))
    assert len(sessions) == 4
    assert sessions[0].title == "Wednesday Registration & Welcome @ Forum Hall Foyer 1st Floor"
    assert (
        sessions[1].title
        == "Embracing Python, AI, and Heuristics: Optimal Paths for Impactful Software"
    )
    assert sessions[2].title == "Learning to code in the age of AI"

    # Test for July 11th
    sessions = await programme_connector.get_sessions_by_date(date(2024, 7, 11))
    assert len(sessions) == 3
    assert sessions[0].title == "Thursday Registration & Welcome @ Forum Hall Foyer 1st Floor"
    assert sessions[1].title == "Why should we all be hyped about inclusive leadership?"
    assert sessions[2].title == "Rapid Prototyping & Proof of Concepts: Django is all we need"

    # Test for July 12th
    sessions = await programme_connector.get_sessions_by_date(date(2024, 7, 12))
    assert len(sessions) == 3
    assert sessions[0].title == "Friday Registration & Welcome @ Forum Hall Foyer 1st Floor"
    assert sessions[1].title == "Healthy code for healthy teams (or the other way around)"
    assert sessions[2].title == "Insights and Experiences of Packaging Python Binary Extensions"

    # Test for a day with no sessions
    sessions = await programme_connector.get_sessions_by_date(date(2024, 7, 13))
    assert len(sessions) == 0


async def test_get_upcoming_sessions(programme_connector, mock_schedule_url):
    programme_connector._api_url = mock_schedule_url

    await programme_connector.fetch_schedule()

    # Please make sure all the sessions have UTC+0 timezone

    # Test with a simulated time in 5 minutes range before a session
    programme_connector._simulated_start_time = datetime(2024, 7, 10, 7, 58, 0, tzinfo=UTC)
    programme_connector._real_start_time = datetime.now(tz=UTC)
    programme_connector._time_multiplier = 1

    upcoming_sessions = await programme_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 1
    assert (
        upcoming_sessions[0].title
        == "Wednesday Registration & Welcome @ Forum Hall Foyer 1st Floor"
    )

    # Test with a simulated time in 5 minutes range where there are 2 upcoming sessions
    programme_connector._simulated_start_time = datetime(2024, 7, 10, 10, 43, 0, tzinfo=UTC)
    upcoming_sessions = await programme_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 2

    # Test with a simulated time before any session in the mock schedule
    programme_connector._simulated_start_time = datetime(2024, 7, 10, 7, 0, 0, tzinfo=UTC)
    upcoming_sessions = await programme_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 0

    # Test with a simulated time after all sessions in the mock schedule
    programme_connector._simulated_start_time = datetime(2024, 7, 11, 11, 20, 0, tzinfo=UTC)
    upcoming_sessions = await programme_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 0

    # Test with a simulated time in 5 minutes range before a break
    programme_connector._simulated_start_time = datetime(2024, 7, 12, 10, 13, 0, tzinfo=UTC)
    upcoming_sessions = await programme_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 0


async def test_fetch_schedule_error_handling(
    programme_connector, unused_tcp_port_factory, aiohttp_client
):
    async def mock_api_handler(request):  # noqa: ARG001 (unused argument)
        return web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    app = web.Application()
    app.router.add_get("/schedule", mock_api_handler)

    server = TestServer(app, port=unused_tcp_port_factory())
    client = await aiohttp_client(server)

    programme_connector._api_url = str(client.make_url("/schedule"))

    await programme_connector.fetch_schedule()

    assert programme_connector.sessions_by_day is None


async def test_get_sessions_by_date_with_empty_schedule(programme_connector):
    sessions = await programme_connector.get_sessions_by_date(date(2024, 7, 10))
    assert len(sessions) == 0


async def test_get_now_with_simulation(programme_connector):
    simulated_start_time = datetime(2024, 7, 10, 8, 0, 0, tzinfo=UTC)
    programme_connector._simulated_start_time = simulated_start_time
    programme_connector._real_start_time = datetime.now(tz=UTC)
    programme_connector._time_multiplier = 60

    # ensure time is ticking between start and finish of this test
    await asyncio.sleep(0.001)

    assert await programme_connector.get_current_time() > simulated_start_time


async def test_get_now_without_simulation(programme_connector):
    now = await programme_connector.get_current_time()

    # ensure time is ticking between start and finish of this test
    await asyncio.sleep(0.001)

    assert datetime.now(tz=UTC) > now
