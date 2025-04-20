import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from pathlib import Path

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from EuroPythonBot.registration.pretix_connector import PretixConnector
from EuroPythonBot.registration.ticket import Ticket

mock_items_file = Path(__file__).parent / "mock_pretix_items.json"
mock_orders_file = Path(__file__).parent / "mock_pretix_orders.json"

PRETIX_API_TOKEN = "MY_PRETIX_API_TOKEN"


@dataclass
class PretixMock:
    base_url: str
    requests: list[Request]


async def create_pretix_app_mock(
    response_factories: dict[str, Callable[[], Response]],
    *,
    port: int | None = None,
    aiohttp_client: Callable[[TestServer], Awaitable[TestClient]],
    unused_tcp_port_factory: Callable[[], int],
) -> PretixMock:
    """
    Create a Pretix mock app with the provided handlers.

    :param response_factories: Map of url paths (e.g. '/items') to response factory functions
    :param port: The port to run on (default: generate random port)
    :param aiohttp_client: Test client generator (fixture from 'pytest-aiohttp')
    :param unused_tcp_port_factory: Random port generator (fixture from 'pytest-asyncio')
    """
    # store all requests to allow introspection
    requests: list[Request] = []

    def make_handler(response_factory):
        async def handler_(request_: Request) -> Response:
            requests.append(request_)
            return response_factory()

        return handler_

    app = web.Application()

    for path, response_factory in response_factories.items():
        app.router.add_get(path, make_handler(response_factory))

    port: int = unused_tcp_port_factory() if port is None else port
    server = TestServer(app, port=port)
    client = await aiohttp_client(server)  # start server

    return PretixMock(base_url=str(client.make_url("")), requests=requests)


@pytest.fixture
async def pretix_mock(aiohttp_client, unused_tcp_port_factory) -> PretixMock:
    return await create_pretix_app_mock(
        response_factories={
            "/items": lambda: web.json_response(
                json.loads(mock_items_file.read_text(encoding="UTF-8"))
            ),
            "/orders": lambda: web.json_response(
                json.loads(mock_orders_file.read_text(encoding="UTF-8"))
            ),
        },
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )


@pytest.mark.asyncio
async def test_pretix_items(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    item_names_by_id = pretix_connector.item_names_by_id

    assert len(item_names_by_id) == 5

    assert item_names_by_id[339041] == "Business"
    assert item_names_by_id[163246] == "Conference"
    assert item_names_by_id[163247] == "Tutorials"
    assert item_names_by_id[339042] == "Personal"
    assert item_names_by_id[163253] == "Combined (Conference + Tutorials)"


@pytest.mark.asyncio
async def test_pretix_orders(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    assert pretix_connector.tickets_by_key == {
        "BR7UH-evanovakova": [
            Ticket(order="BR7UH", name="Eva Nováková", type="Business", variation="Conference")
        ],
        "BR7UH-jannovak": [
            Ticket(order="BR7UH", name="Jan Novák", type="Business", variation="Tutorials")
        ],
        "RCZN9-maijameikalainen": [
            Ticket(order="RCZN9", name="Maija Meikäläinen", type="Personal", variation=None)
        ],
    }


async def test_get_ticket(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    tickets = pretix_connector.get_tickets(order="BR7UH", name="Eva Nováková")

    assert tickets == [
        Ticket(order="BR7UH", name="Eva Nováková", type="Business", variation="Conference")
    ]


async def test_cache(pretix_mock, tmp_path):
    pretix_connector_1 = PretixConnector(
        url=pretix_mock.base_url, token=PRETIX_API_TOKEN, cache_file=tmp_path / "pretix_cache.json"
    )
    assert not pretix_connector_1.item_names_by_id
    assert not pretix_connector_1.tickets_by_key

    # fetch data in connector 1
    await pretix_connector_1.fetch_pretix_data()
    assert pretix_connector_1.item_names_by_id
    assert pretix_connector_1.tickets_by_key

    pretix_connector_2 = PretixConnector(
        url=pretix_mock.base_url, token=PRETIX_API_TOKEN, cache_file=tmp_path / "pretix_cache.json"
    )
    assert pretix_connector_1.item_names_by_id == pretix_connector_2.item_names_by_id
    assert pretix_connector_1.tickets_by_key == pretix_connector_2.tickets_by_key


async def test_get_ticket_handles_ticket_ids(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    tickets = pretix_connector.get_tickets(order="#BR7UH-3", name="Eva Nováková")

    assert tickets == [
        Ticket(order="BR7UH", name="Eva Nováková", type="Business", variation="Conference")
    ]


async def test_get_ticket_ignores_accents(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    tickets = pretix_connector.get_tickets(order="BR7UH", name="Jan Novak")

    assert tickets == [
        Ticket(order="BR7UH", name="Jan Novák", type="Business", variation="Tutorials")
    ]


async def test_get_ticket_ignores_name_order(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    tickets = pretix_connector.get_tickets(order="RCZN9", name="Meikäläinen Maija")

    assert tickets == [
        Ticket(order="RCZN9", name="Maija Meikäläinen", type="Personal", variation=None)
    ]


async def test_get_ticket_returns_none_on_unknown_input(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    tickets = pretix_connector.get_tickets(order="ABC01", name="John Doe")

    assert tickets == []


async def test_get_ticket_ignores_unpaid_orders(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    tickets = pretix_connector.get_tickets(order="PFZBT", name="Erika Mustermann")

    assert tickets == []


async def test_positions_without_name_are_ignored(aiohttp_client, unused_tcp_port_factory):
    pretix_mock = await create_pretix_app_mock(
        response_factories={
            "/items": lambda: web.json_response(
                json.loads(mock_items_file.read_text(encoding="UTF-8"))
            ),
            "/orders": lambda: web.json_response(
                {
                    "next": None,
                    "results": [
                        {
                            "code": "ABC01",
                            "status": "p",
                            "positions": [
                                {
                                    "order": "ABC01",
                                    "item": 339041,
                                    "variation": None,
                                    "attendee_name": None,
                                }
                            ],
                        }
                    ],
                }
            ),
        },
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )

    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    assert pretix_connector.tickets_by_key == {}


async def test_pagination(aiohttp_client, unused_tcp_port_factory):
    # split items response into two pages
    port = unused_tcp_port_factory()
    base_url = f"http://127.0.0.1:{port}"

    pretix_mock = await create_pretix_app_mock(
        {
            "/items": lambda: web.json_response(
                {
                    "next": f"{base_url}/items2",
                    "results": [
                        {
                            "id": 339041,
                            "name": {"en": "Business"},
                            "variations": [
                                {"id": 163246, "value": {"en": "Conference"}},
                                {"id": 163247, "value": {"en": "Tutorials"}},
                            ],
                        }
                    ],
                }
            ),
            "/items2": lambda: web.json_response(
                {
                    "next": None,
                    "results": [
                        {
                            "id": 339042,
                            "name": {"en": "Personal"},
                            "variations": [
                                {
                                    "id": 163253,
                                    "value": {"en": "Combined (Conference + Tutorials)"},
                                },
                            ],
                        }
                    ],
                }
            ),
            "/orders": lambda: web.json_response(
                json.loads(mock_orders_file.read_text(encoding="UTF-8"))
            ),
        },
        port=port,
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )

    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)
    await pretix_connector.fetch_pretix_data()

    assert len(pretix_connector.item_names_by_id) == 5, (
        "Only the first page of '/items' was fetched."
    )


@pytest.mark.asyncio
async def test_consecutive_fetches_are_prevented(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)
    requests = pretix_mock.requests

    # initial fetch should fetch everything
    await pretix_connector.fetch_pretix_data()

    assert len(requests) == 2
    assert requests[0].url.path == "/items"
    assert requests[1].url.path == "/orders"

    # second fetch should do nothing
    requests.clear()
    await pretix_connector.fetch_pretix_data()

    assert len(requests) == 0


@pytest.mark.asyncio
async def test_consecutive_fetches_after_some_time_fetch_updates(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)
    requests = pretix_mock.requests

    initial_time = datetime.now(tz=UTC)

    # initial fetch should fetch everything
    await pretix_connector.fetch_pretix_data()

    assert len(requests) == 2
    assert requests[0].url.path == "/items"
    assert requests[1].url.path == "/orders"

    # fetch after >2 minutes should fetch updates
    three_minutes_before = initial_time - timedelta(minutes=3)
    pretix_connector._last_fetch = three_minutes_before

    requests.clear()
    await pretix_connector.fetch_pretix_data()

    assert len(requests) == 2
    assert requests[0].url.path == "/items"
    assert requests[1].url.path == "/orders"
    assert datetime.fromisoformat(requests[1].url.query["modified_since"]) == three_minutes_before


@pytest.mark.asyncio
async def test_api_error_responses_are_raised(aiohttp_client, unused_tcp_port_factory):
    pretix_mock = await create_pretix_app_mock(
        response_factories={
            "/items": lambda: web.json_response(
                {"error": "Crash"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            ),
            "/orders": lambda: web.json_response(
                json.loads(mock_orders_file.read_text(encoding="UTF-8"))
            ),
        },
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )

    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    with pytest.raises(aiohttp.ClientResponseError) as e:
        await pretix_connector.fetch_pretix_data()

    assert e.value.status == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_multiple_tickets(aiohttp_client, unused_tcp_port_factory):
    pretix_mock = await create_pretix_app_mock(
        {
            "/items": lambda: web.json_response(
                {
                    "next": None,
                    "results": [
                        {"id": 123, "name": {"en": "Business"}, "variations": []},
                        {"id": 456, "name": {"en": "Speaker's Dinner"}, "variations": []},
                    ],
                }
            ),
            "/orders": lambda: web.json_response(
                {
                    "next": None,
                    "results": [
                        {
                            "code": "BR7UH",
                            "status": "p",
                            "positions": [
                                {
                                    "order": "BR7UH",
                                    "item": 123,
                                    "variation": None,
                                    "attendee_name": "Jane Doe",
                                },
                                {
                                    "order": "BR7UH",
                                    "item": 456,
                                    "variation": None,
                                    "attendee_name": "Jane Doe",
                                },
                            ],
                        },
                    ],
                }
            ),
        },
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )

    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)
    await pretix_connector.fetch_pretix_data()

    tickets = pretix_connector.get_tickets(order="BR7UH", name="Jane Doe")

    assert set(tickets) == {
        Ticket(order="BR7UH", name="Jane Doe", type="Business", variation=None),
        Ticket(order="BR7UH", name="Jane Doe", type="Speaker's Dinner", variation=None),
    }


async def test_cancelled_orders_are_removed(aiohttp_client, unused_tcp_port_factory):
    pretix_mock = await create_pretix_app_mock(
        response_factories={
            "/items": lambda: web.json_response(json.loads(mock_items_file.read_text())),
            "/orders": lambda: web.json_response(
                {
                    "next": None,
                    "results": [
                        {
                            "code": "ABC01",
                            "status": "c",  # cancelled
                            "positions": [
                                {
                                    "order": "ABC01",
                                    "item": 339041,
                                    "variation": None,
                                    "attendee_name": "Jane Doe",
                                }
                            ],
                        }
                    ],
                }
            ),
        },
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )

    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    # insert previously paid ticket
    ticket = Ticket(order="ABC01", name="Jane Doe", type="Business", variation=None)
    pretix_connector.tickets_by_key[ticket.key] = [ticket]

    # fetch pretix data: ticket was cancelled
    await pretix_connector.fetch_pretix_data()

    assert pretix_connector.tickets_by_key == {}
