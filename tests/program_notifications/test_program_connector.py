import json
import time
from datetime import date, datetime, timezone
from http import HTTPStatus
from pathlib import Path

import aiofiles
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from program_notifications.program_connector import ProgramConnector

mock_schedule_file = Path(__file__).parent / "mock_schedule.json"


@pytest.fixture
def mock_schedule():
    with mock_schedule_file.open() as f:
        return json.load(f)


@pytest.fixture
def cache_file(tmp_path):
    return tmp_path / "cache.json"


@pytest.fixture
async def program_connector(cache_file):
    return ProgramConnector(
        api_url="http://test.api/schedule", timezone_offset=0, cache_file=cache_file
    )


@pytest.fixture
async def mock_client(aiohttp_client, unused_tcp_port_factory, mock_schedule):
    async def mock_api_handler(request):
        return web.json_response(mock_schedule)

    app = web.Application()
    app.router.add_get("/schedule", mock_api_handler)

    server = TestServer(app, port=unused_tcp_port_factory())
    client = await aiohttp_client(server)

    return client


@pytest.fixture
async def mock_schedule_url(mock_client):
    return str(mock_client.make_url("/schedule"))


@pytest.mark.asyncio
async def test_parse_schedule(program_connector, mock_schedule):
    sessions_by_day = await program_connector.parse_schedule(mock_schedule)

    assert len(sessions_by_day) == 2

    assert len(sessions_by_day[date(2024, 10, 4)]) == 4
    assert len(sessions_by_day[date(2024, 10, 5)]) == 3


@pytest.mark.asyncio
async def test_fetch_schedule(program_connector, mock_schedule_url, cache_file, mock_schedule):
    program_connector._api_url = mock_schedule_url

    await program_connector.fetch_schedule()

    async with aiofiles.open(cache_file, "r") as f:
        cached_data = json.loads(await f.read())
        assert cached_data == mock_schedule


@pytest.mark.asyncio
async def test_get_schedule_from_cache(program_connector, mock_schedule, cache_file):
    async with aiofiles.open(cache_file, "w") as f:
        await f.write(json.dumps(mock_schedule))

    sessions_by_day = await program_connector._get_schedule_from_cache()

    assert len(sessions_by_day) == 2
    assert len(sessions_by_day[date(2024, 10, 4)]) == 4
    assert len(sessions_by_day[date(2024, 10, 5)]) == 3


@pytest.mark.asyncio
async def test_get_sessions_by_date(program_connector, mock_schedule_url):
    program_connector._api_url = mock_schedule_url

    await program_connector.fetch_schedule()

    # Test for July 10th
    sessions = await program_connector.get_sessions_by_date(date(2024, 10, 4))
    assert len(sessions) == 4
    assert sessions[0].title == "Acreditaciones | Accreditations"
    assert sessions[1].title == "Superando el reto del billón de filas con Python"
    assert (
        sessions[2].title
        == "Pattern busters: encontrando patrones significativos con Python en aplicaciones reales"
    )

    # Test for July 11th
    sessions = await program_connector.get_sessions_by_date(date(2024, 10, 5))
    assert len(sessions) == 3
    assert sessions[0].title == "Acreditaciones | Accreditations"
    assert sessions[1].title == "Apertura del evento | Event opening"
    assert sessions[2].title == "Modelando el efecto de las sombras en un sistema fotovoltaico"

    # Test for a day with no sessions
    sessions = await program_connector.get_sessions_by_date(date(2024, 10, 8))
    assert len(sessions) == 0


@pytest.mark.asyncio
async def test_get_upcoming_sessions(program_connector, mock_schedule_url):
    program_connector._api_url = mock_schedule_url

    await program_connector.fetch_schedule()

    # Please make sure all the sessions have UTC+0 timezone

    # Test with a simulated time in 5 minutes range before a session
    program_connector._simulated_start_time = datetime(2024, 10, 5, 7, 58, 0, tzinfo=timezone.utc)
    program_connector._real_start_time = datetime.now(tz=timezone.utc)
    program_connector._time_multiplier = 1

    upcoming_sessions = await program_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 1
    assert (
        upcoming_sessions[0].title
        == "Acreditaciones | Accreditations"
    )

    # Test with a simulated time in 5 minutes range where there are 2 upcoming sessions
    program_connector._simulated_start_time = datetime(2024, 10, 5, 11, 12, 0, tzinfo=timezone.utc)
    upcoming_sessions = await program_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 2

    # Test with a simulated time before any session in the mock schedule
    program_connector._simulated_start_time = datetime(2024, 10, 5, 7, 0, 0, tzinfo=timezone.utc)
    upcoming_sessions = await program_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 0

    # Test with a simulated time after all sessions in the mock schedule
    program_connector._simulated_start_time = datetime(2024, 10, 5, 20, 20, 0, tzinfo=timezone.utc)
    upcoming_sessions = await program_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 0

    # Test with a simulated time in 5 minutes range before a break
    program_connector._simulated_start_time = datetime(2024, 10, 5, 10, 43, 0, tzinfo=timezone.utc)
    upcoming_sessions = await program_connector.get_upcoming_sessions()
    assert len(upcoming_sessions) == 0


@pytest.mark.asyncio
async def test_fetch_schedule_error_handling(
    program_connector, unused_tcp_port_factory, aiohttp_client
):
    async def mock_api_handler(request):
        return web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    app = web.Application()
    app.router.add_get("/schedule", mock_api_handler)

    server = TestServer(app, port=unused_tcp_port_factory())
    client = await aiohttp_client(server)

    program_connector._api_url = str(client.make_url("/schedule"))

    await program_connector.fetch_schedule()

    assert program_connector.sessions_by_day is None


@pytest.mark.asyncio
async def test_get_sessions_by_date_with_empty_schedule(program_connector):
    sessions = await program_connector.get_sessions_by_date(date(2024, 7, 10))
    assert len(sessions) == 0


@pytest.mark.asyncio
async def test_get_now_with_simulation(program_connector):
    simulated_start_time = datetime(2024, 7, 10, 8, 0, 0, tzinfo=timezone.utc)
    program_connector._simulated_start_time = simulated_start_time
    program_connector._real_start_time = datetime.now(tz=timezone.utc)
    program_connector._time_multiplier = 60

    # ensure time is ticking between start and finish of this test
    time.sleep(0.001)

    assert await program_connector._get_now() > simulated_start_time


@pytest.mark.asyncio
async def test_get_now_without_simulation(program_connector):
    now = await program_connector._get_now()

    # ensure time is ticking between start and finish of this test
    time.sleep(0.001)

    assert datetime.now(tz=timezone.utc) > now
