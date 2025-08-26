import json
import pathlib
from collections.abc import Callable
from unittest import mock

import arrow
import pytest

from discord_bot.extensions.programme_notifications.domain import europython
from discord_bot.extensions.programme_notifications.services import api
from tests.programme_notifications import factories


@pytest.mark.parametrize(
    ("bytes_from_data_file", "expected_schedule"),
    [
        pytest.param(
            "pretalx_one_session.testdata.json",
            europython.Schedule(
                sessions=[
                    europython.Session(
                        id=101,
                        start=arrow.get("2023-07-21T12:30:00+02:00").to("Europe/Prague"),
                        submission=europython.Submission(
                            code="ABABAB",
                            speakers=[
                                europython.Speaker(
                                    code="ABCDEF",
                                    name="John Johnson",
                                    avatar_url="https://my.avatar/john.jpg",
                                ),
                                europython.Speaker(
                                    code="ABCDEG",
                                    name="Carl Carlsson",
                                    avatar_url="https://my.avatar/carl.jpg",
                                ),
                            ],
                            title="Stop using globals!",
                            track=europython.Track(
                                id=3571,
                                name=europython.TranslatedString("Python Basics"),
                            ),
                            abstract="Globalization of your Python code is bad for you!",
                            duration=30,
                        ),
                        room=europython.Room(
                            id=1234,
                            name=europython.TranslatedString("The Great Outdoors"),
                        ),
                        description=europython.TranslatedString("You should pass more often and then return."),
                        duration=30,
                        url=None,
                    )
                ],
                version="0.10",
                schedule_hash="44752d956c3ec10d2379ebcce94a05fadecc7dc1",
                breaks=[],
            ),
            id="one schedule, no breaks",
        ),
        pytest.param(
            "pretalx_empty_schedule.testdata.json",
            europython.Schedule(
                sessions=[],
                version="0.10",
                schedule_hash="9a9906d3d184ee70e2c3ab59b1ea86f022dfb38f",
                breaks=[],
            ),
            id="empty schedule",
        ),
        pytest.param(
            "pretalx_one_break.testdata.json",
            europython.Schedule(
                sessions=[
                    europython.Session(
                        id=201,
                        start=arrow.get("2023-07-17T11:00:00+02:00").to("Europe/Prague"),
                        duration=15,
                        description=europython.TranslatedString("Coffee Break"),
                        room=europython.Room(
                            id=2184,
                            name=europython.TranslatedString("Club B"),
                        ),
                        submission=None,
                        url=None,
                    )
                ],
                version="0.10",
                schedule_hash="1a063fe29da98b9934353dc28fbd24b21b7f0487",
                breaks=[],
            ),
            id="one break, no session",
        ),
        pytest.param(
            "pretalx_session_with_null_values.testdata.json",
            europython.Schedule(
                sessions=[
                    europython.Session(
                        id=401,
                        start=arrow.get("2023-07-21T12:30:00+02:00").to("Europe/Prague"),
                        submission=europython.Submission(
                            code="ALPLOA",
                            title="The scientific journey",
                            speakers=[europython.Speaker(code="STEVEB", name="Steve Bytheway", avatar_url=None)],
                            abstract="Around the world in 1.5 days.",
                            track=None,
                            duration=None,
                        ),
                        room=europython.Room(
                            id=2191,
                            name=europython.TranslatedString("South Hall 2B"),
                        ),
                        description=europython.TranslatedString("Fast!"),
                        url=None,
                    )
                ],
                version="0.10",
                schedule_hash="125711eaf19f97ece4d773162cca276b71f1c29d",
                breaks=[],
            ),
            id="session with all optional values as null",
        ),
    ],
    indirect=["bytes_from_data_file"],
)
@pytest.mark.asyncio
async def test_api_client_returns_schedule_instance(
    bytes_from_data_file: bytes,
    expected_schedule: europython.Schedule,
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
) -> None:
    """Getting the same response again results in the same hash."""
    # GIVEN a session that returns a fixed, stubbed get response
    client_session.get.return_value.__aenter__.return_value.read = mock.AsyncMock(return_value=bytes_from_data_file)
    # AND a configuration repository with a pretalx schedule url
    config = configuration_factory({"pretalx_schedule_url": "https://europython.api/schedule/latest"})

    # AND an api client with that session and configuration repository
    client = api.ApiClient(session=client_session, config=config)

    # WHEN the schedule is fetched from the API
    response = await client.fetch_schedule()

    # THEN the returned response includes the expected schedule
    assert response == api.ScheduleResponse(schedule=expected_schedule, from_cache=False)


@pytest.mark.parametrize(
    "bytes_from_data_file",
    [
        "pretalx_schedule_response_20230701.testdata.json",
        "pretalx_schedule_response_20230714.testdata.json",
    ],
    indirect=["bytes_from_data_file"],
)
@pytest.mark.asyncio
async def test_api_client_handles_actual_response(
    bytes_from_data_file: bytes,
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
) -> None:
    """The API client handles a cached version of an actual response."""
    # GIVEN a session that returns a cached realistic response
    client_session.get.return_value.__aenter__.return_value.read = mock.AsyncMock(return_value=bytes_from_data_file)
    # AND a configuration repository with a pretalx schedule url
    config = configuration_factory({"pretalx_schedule_url": "https://schedule.pretalx"})
    # AND an api client with that session and configuration repository
    client = api.ApiClient(session=client_session, config=config)

    # WHEN the schedule is fetched
    response = await client.fetch_schedule()

    # THEN the API client returns a non-cached response
    assert not response.from_cache
    # AND the response has a schedule
    schedule = response.schedule
    assert isinstance(schedule, europython.Schedule)
    # AND the schedule contains the expected number of sessions
    assert len(schedule.sessions) == len(json.loads(bytes_from_data_file)["slots"])
    # AND the schedule contains the expected number of breaks
    # assert len(schedule.breaks) == len(json.loads(bytes_from_data_file)["breaks"])


@pytest.mark.asyncio
async def test_schedule_hash_is_identical_if_pretalx_response_is_identical(
    pretalx_response_stub: bytes,
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
) -> None:
    """Getting the same response again results in the same hash."""
    # GIVEN a session that returns a fixed, stubbed get response
    client_session.get.return_value.__aenter__.return_value.read = mock.AsyncMock(return_value=pretalx_response_stub)
    # AND a configuration repository with a pretalx schedule url
    config = configuration_factory({"pretalx_schedule_url": "https://schedule.pretalx"})
    # AND an api client with that session and configuration repository
    client = api.ApiClient(session=client_session, config=config)
    # AND a first response of a schedule fetch
    first_response = await client.fetch_schedule()

    # WHEN the schedule is fetched a second time
    second_response = await client.fetch_schedule()

    # THEN the schedule hash is the same as the initial schedule
    assert first_response.schedule.schedule_hash == second_response.schedule.schedule_hash


@pytest.mark.asyncio
async def test_client_ignores_session_with_invalid_structure(
    get_bytes_from_data_file: Callable[[str], bytes],
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
) -> None:
    """Invalid slots don't break the application but are ignored."""
    # GIVEN a session that returns a fixed, stubbed get response
    client_session.get.return_value.__aenter__.return_value.read = mock.AsyncMock(
        return_value=get_bytes_from_data_file("pretalx_with_invalid_slot.testdata.json")
    )
    # AND a configuration repository with a pretalx schedule url
    config = configuration_factory({"pretalx_schedule_url": "https://schedule.pretalx"})
    # AND an api client with that session and configuration repository
    client = api.ApiClient(session=client_session, config=config)

    # WHEN the schedule is fetched
    response = await client.fetch_schedule()

    # THEN the invalid session was ignored
    assert not response.schedule.sessions


@pytest.mark.asyncio
async def test_fetch_schedule_returns_cached_schedule_on_api_error(
    get_data_file_path: Callable[[str], pathlib.Path],
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
) -> None:
    """If the call to Pretalx fails, return a cached schedule."""
    # GIVEN a session that fails on a get response
    client_session.get.return_value.__aenter__.return_value.read = mock.AsyncMock(side_effect=Exception)
    # AND a configuration repository with a pretalx schedule url
    config = configuration_factory({"pretalx_schedule_url": "https://schedule.pretalx"})
    # AND an api client with a known schedule cache path
    client = api.ApiClient(
        session=client_session,
        config=config,
        schedule_cache_path=get_data_file_path("pretalx_one_session.testdata.json"),  # pyright: ignore[reportCallIssue]
    )

    # WHEN the schedule is fetched
    response = await client.fetch_schedule()

    # THEN the response contains a cached schedule
    assert response.from_cache
    # AND the schedule is as expected
    assert response.schedule == europython.Schedule(
        sessions=[
            europython.Session(
                id=101,
                start=arrow.Arrow(
                    year=2023,
                    month=7,
                    day=21,
                    hour=12,
                    minute=30,
                    second=0,
                    tzinfo="Europe/Prague",
                ),
                submission=europython.Submission(
                    code="ABABAB",
                    speakers=[
                        europython.Speaker(
                            code="ABCDEF",
                            name="John Johnson",
                            avatar_url="https://my.avatar/john.jpg",
                        ),
                        europython.Speaker(
                            code="ABCDEG",
                            name="Carl Carlsson",
                            avatar_url="https://my.avatar/carl.jpg",
                        ),
                    ],
                    title="Stop using globals!",
                    track=europython.Track(
                        id=3571,
                        name=europython.TranslatedString("Python Basics"),
                    ),
                    abstract="Globalization of your Python code is bad for you!",
                    duration=30,
                ),
                room=europython.Room(
                    id=1234,
                    name=europython.TranslatedString("The Great Outdoors"),
                ),
                description=europython.TranslatedString("You should pass more often and then return."),
                duration=30,
                url=None,
            )
        ],
        version="0.10",
        schedule_hash="44752d956c3ec10d2379ebcce94a05fadecc7dc1",
        breaks=[],
    )


def test_instantiating_api_client_with_non_existing_cache_path_fails(
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
) -> None:
    """There should be a fallback schedule cache file."""
    # GIVEN a non-existing file cache path
    non_existing_path = pathlib.Path("/non/existing/path/schedule.json")

    # WHEN an api client is initialized with that path
    # THEN instantiating the client fails
    with pytest.raises(ValueError):
        api.ApiClient(
            session=client_session,
            config=configuration_factory({}),
            schedule_cache_path=non_existing_path, # pyright: ignore[reportCallIssue]
        )
