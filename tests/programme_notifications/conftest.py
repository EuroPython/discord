from collections.abc import Callable
from typing import Any
from unittest import mock

import aiohttp
import arrow
import cattrs
import pytest
import yarl
from _pytest import pathlib

from discord_bot.extensions.programme_notifications import configuration
from discord_bot.extensions.programme_notifications.domain import europython
from tests.programme_notifications import factories

_DATA_DIR = pathlib.Path(__file__).parent.joinpath("_data")


@pytest.fixture()
def bytes_from_data_file(request: pytest.FixtureRequest) -> bytes:
    """Return bytes from a test _data file for a parameterized test."""
    return _get_data_file(request.param)


@pytest.fixture()
def get_bytes_from_data_file() -> Callable[[str], bytes]:
    """Allow tests to retrieve bytes from test _data files."""
    return _get_data_file


@pytest.fixture()
def get_data_file_path() -> Callable[[str], pathlib.Path]:
    """Get the path to a datafile."""
    return _get_data_file_path


def _get_data_file(filename: str) -> bytes:
    """Get a _data file from the test _data directory."""
    return _get_data_file_path(filename).read_bytes()


def _get_data_file_path(filename: str) -> pathlib.Path:
    """Get the path to a datafile."""
    return _DATA_DIR.joinpath(filename)


@pytest.fixture()
def pretalx_response_stub() -> bytes:
    """Get a pretalx response stub with an actual cached response."""
    return _get_data_file("pretalx_schedule_response_20230701.testdata.json")


@pytest.fixture()
def europython_response_stub(request: pytest.FixtureRequest) -> bytes:
    """Get a pretalx response stub with an actual cached response."""
    identifier = getattr(request, "param", "session_response_20230702")
    return _get_data_file(f"europython_{identifier}.testdata.json")


@pytest.fixture()
def client_session() -> mock.Mock:
    """Return a client session mock factory.

    :return: A factory to create an `aiohttp.ClientSession` mock.
    """
    session_cls = mock.create_autospec(spec=aiohttp.ClientSession, spec_set=True)
    return session_cls()


@pytest.fixture()
def configuration_factory() -> factories.ConfigurationFactory:
    """Return a configuration factory with default values.

    :return: The configuration factory callable
    """
    return _configuration_factory


def _configuration_factory(config: dict[str, Any]) -> configuration.NotifierConfiguration:
    """Create a stubbed configuration and return a configuration repo.

    :param config: The configuration to use
    :return: An in-memory configuration repository
    """
    _configuration_defaults = {
        "timezone": "Europe/Berlin",
        "conference_days_first": "2024-04-22",
        "conference_days_last": "2024-04-24",
        "conference_afternoon_session_start_time": 13,
        "conference_name": "PyCon DE & PyData Berlin 2024",
        "conference_website": "https://2024.pycon.de",
        "pretalx_talk_url": "https://2024.pycon.de/program/{code}",
        "pretalx_schedule_url": ("https://pretalx.com/api/events/pyconde-pydata-2024/schedules/latest/"),
        "video_url": "https://app.sli.do/event/test",
        "notification_channels": [
            {"webhook_id": "PROGRAMME_NOTIFICATIONS", "include_channel_in_embeds": True},
        ],
        "webhooks": {
            "EP2023_NOTIFICATIONS_CHANNEL-channel": "https://webhook.discord/123",
            # "PYTHON_DISCORD-channel": "https://webhook.discord/456",
            "ROOM_1234": "https://webhook.discord/abacd",
            "ROOM_5432": "https://webhook.discord/dcbea",
        },
        "rooms": {
            "1234": {
                "discord_channel_id": "1120780288755253338",
                "webhook_id": "ROOM_1234",
                "livestreams": {
                    "2024-04-22": "https://2024.pycon.de/live",
                    "2024-04-23": "https://2024.pycon.de/live",
                    "2024-04-24": "https://2024.pycon.de/live",
                },
            },
            "4567": {
                "discord_channel_id": "1120780345575477421",
                "webhook_id": "ROOM_4567",
                "livestreams": {
                    "2024-04-22": "https://2024.pycon.de/live",
                    "2024-04-23": "https://2024.pycon.de/live",
                    "2024-04-24": "https://2024.pycon.de/live",
                },
            },
            "8901": {
                "discord_channel_id": "1120780371622121612",
                "webhook_id": "ROOM_8901",
                "livestreams": {
                    "2024-04-22": "https://2024.pycon.de/live",
                    "2024-04-23": "https://2024.pycon.de/live",
                    "2024-04-24": "https://2024.pycon.de/live",
                },
            },
            "2345": {
                "discord_channel_id": "1120780401791750315",
                "webhook_id": "ROOM_2345",
                "livestreams": {
                    "2024-04-22": "https://2024.pycon.de/live",
                    "2024-04-23": "https://2024.pycon.de/live",
                    "2024-04-24": "https://2024.pycon.de/live",
                },
            },
            "6789": {
                "discord_channel_id": "1120780461195657387",
                "webhook_id": "ROOM_6789",
                "livestreams": {
                    "2024-04-22": "https://2024.pycon.de/live",
                    "2024-04-23": "https://2024.pycon.de/live",
                    "2024-04-24": "https://2024.pycon.de/live",
                },
            },
            "1111": {
                "discord_channel_id": "1120780490576777287",
                "webhook_id": "ROOM_111",
                "livestreams": {
                    "2024-04-22": "https://2024.pycon.de/live",
                    "2024-04-23": "https://2024.pycon.de/live",
                    "2024-04-24": "https://2024.pycon.de/live",
                },
            },
        },
    }
    kwargs = _configuration_defaults | config
    converter = cattrs.Converter()
    converter.register_structure_hook(yarl.URL, lambda v, t: t(v))
    converter.register_structure_hook(arrow.Arrow, lambda v, _: arrow.get(v))
    return converter.structure(kwargs, configuration.NotifierConfiguration)


@pytest.fixture()
def session_factory() -> factories.SessionFactory:
    """Return a session factory."""
    return _session_factory


@pytest.fixture()
def sessions(request: pytest.FixtureRequest) -> list[europython.Session]:
    """Return a session factory that takes a list of dicts."""
    session_dicts = getattr(request, "param", [])
    return [_session_factory(**d) for d in session_dicts]


def _session_factory(**attributes) -> europython.Session:
    """Create a Session instance.

    :param attributes: Kwargs to be combined with default attributes
    :return: An instance of `europython.Session` with the specified
      attributes, combined with default attributes for unspecified
      attributes.
    """
    # Defaults for nested structure
    defaults = {
        "id": 1,
        "start": "2023-07-19T09:55:00+02:00",
        "duration": 45,
        "description": {"en": None},
        "room": {
            "id": 1234,
            "name": {"en": "The Broom Closet"},
        },
        "submission": {
            "code": "ABCDEF",
            "title": "A Tale of Two Pythons: Subinterpreters in Action!",
            "abstract": (
                "Sometimes, having one, undivided interpreter just isn't enough. The pesky GIL,"
                " problems with isolation, and the difficult problem of concurrency haunt the dreams of"
                " even the most talented Python developer. Clearly, a good solution is needed and that"
                " solution is finally here: subinterpreters."
            ),
            "speakers": [
                {"code": "AB34EF", "name": "Ada Lovelace", "avatar_url": "https://ada.avatar"}
            ],
            "duration": 45,
            "track": {"id": 1, "name": {"en": "Core Python"}},
        },
        "url": "https://europython/sessions/a-tale-of-two-pythons",
        "experience": None,
        "livestream_url": None,
        "discord_channel_id": None,
        "q_and_a_url": None,
    }
    # Allow test overrides to update nested fields
    import copy
    merged = copy.deepcopy(defaults)
    # Map top-level overrides into nested submission dict if needed
    submission_keys = ["title", "abstract", "speakers", "track", "duration", "code"]
    for k, v in attributes.items():
        if k in ["room"] and isinstance(v, dict):
            merged[k].update(v)
        elif k in ["submission"] and isinstance(v, dict):
            merged[k].update(v)
        elif k in ["url", "livestream_url", "q_and_a_url"] and v is not None:
            merged[k] = str(v)
        elif k in submission_keys:
            # Special handling for track: allow None or dict
            if k == "track":
                if v is None:
                    merged["submission"]["track"] = None
                elif isinstance(v, dict):
                    # If only {"en": ...} is provided, wrap in id=1
                    if "en" in v and len(v) == 1:
                        merged["submission"]["track"] = {"id": 1, "name": v}
                    else:
                        merged["submission"]["track"] = v
                else:
                    merged["submission"]["track"] = v
            elif k == "speakers":
                merged["submission"]["speakers"] = v
            elif k == "duration":
                merged["submission"]["duration"] = v
                merged["duration"] = v
            else:
                merged["submission"][k] = v
        else:
            merged[k] = v
    converter = cattrs.Converter()
    converter.register_structure_hook(arrow.Arrow, lambda v, _: arrow.get(v))
    converter.register_structure_hook(yarl.URL, lambda v, t: t(v))
    return converter.structure(merged, europython.Session)
