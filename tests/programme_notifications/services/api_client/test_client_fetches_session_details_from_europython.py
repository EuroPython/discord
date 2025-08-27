# import json
from collections.abc import Callable
from unittest import mock

import pytest
import yarl

from discord_bot.extensions.programme_notifications.services import api
from tests.programme_notifications import factories


@pytest.mark.parametrize(
    ("session_id", "expected_session_url", "expected_experience_level"),
    [
        pytest.param(
            "BHXSQU",
            yarl.URL("https://2024.pycon.de/program/BHXSQU"),
            "intermediate",
        ),
        pytest.param(
            "9GJFZZ",
            yarl.URL("https://2024.pycon.de/program/9GJFZZ"),
            "advanced",
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_client_returns_level_and_url_for_session(
    session_id: str,
    expected_session_url: yarl.URL,
    expected_experience_level: str,
    get_bytes_from_data_file: Callable[[str], bytes],
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
) -> None:
    """These details are fetched from a secondary API.

    To prevent making too many API calls at once, these details are only
    fetched when the notifications are being sent. Otherwise, we'd have
    to make an API call to the EuroPython website for each session at
    scheduling time.
    """
    # GIVEN a session that returns a fixed, stubbed get response
    # client_session.get.return_value.__aenter__.return_value.json = mock.AsyncMock(
    #     return_value=json.loads(get_bytes_from_data_file(f"europython_{session_id}.testdata.json"))
    # )
    client_session.get.return_value.__aenter__.return_value.text = mock.AsyncMock(
        return_value=f"bla bla Expected audience expertise: Domain: <p>{expected_experience_level}</p> bla bla",
    )
    # AND a configuration repository with a pretalx schedule url
    config = configuration_factory(
        {
            "pretalx_talk_url": "https://2024.pycon.de/program/{code}",
            # "conference_website_api_session_url": "https://2024.pycon.de/program/{code}",
            # "conference_website_session_base_url": "https://2024.pycon.de/program/{slug}",
        }
    )
    # AND an api client with that session and configuration repository
    client = api.ApiClient(session=client_session, config=config)

    # WHEN session information is fetched from the API
    session_url, experience = await client.fetch_session_details(code=session_id)

    # THEN the slug returned is the expected slug
    assert session_url == expected_session_url
    # AND the experience returned is the expected experience level
    assert experience == expected_experience_level
    # AND the api client used the appropriate arguments
    # client_session.get.assert_called_with(
    #     url=f"https://europython.api/api/session/{session_id}", raise_for_status=True
    # )
