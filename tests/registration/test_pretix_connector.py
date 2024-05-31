import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from registration.pretix_connector import PretixConnector
from registration.ticket import Ticket

mock_items_file = Path(__file__).parent / "mock_pretix_items.json"
mock_orders_file = Path(__file__).parent / "mock_pretix_orders.json"

PRETIX_API_TOKEN = "MY_PRETIX_API_TOKEN"


@dataclass
class PretixMock:
    base_url: str
    requests: list[Request]
    client: TestClient
    server: TestServer


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

    return PretixMock(
        base_url=str(client.make_url("")), requests=requests, client=client, server=server
    )


@pytest.fixture()
async def pretix_mock(aiohttp_client, unused_tcp_port_factory) -> PretixMock:
    return await create_pretix_app_mock(
        response_factories={
            "/items": lambda: web.json_response(json.loads(mock_items_file.read_text())),
            "/orders": lambda: web.json_response(json.loads(mock_orders_file.read_text())),
        },
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )


@pytest.mark.asyncio
async def test_pretix_items(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    items_by_id = pretix_connector.items_by_id

    assert len(items_by_id) == 5

    assert items_by_id[339041].names_by_locale["en"] == "Business"
    assert items_by_id[163246].names_by_locale["en"] == "Conference"
    assert items_by_id[163247].names_by_locale["en"] == "Tutorials"
    assert items_by_id[339042].names_by_locale["en"] == "Personal"
    assert items_by_id[163253].names_by_locale["en"] == "Combined (Conference + Tutorials)"


@pytest.mark.asyncio
async def test_pretix_orders(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    assert pretix_connector.tickets_by_key == {
        "BR7UH-evanovakova": Ticket(order="BR7UH", name="Eva Nováková", type="Business"),
        "BR7UH-jannovak": Ticket(order="BR7UH", name="Jan Novák", type="Business"),
        "RCZN9-maijameikalainen": Ticket(order="RCZN9", name="Maija Meikäläinen", type="Personal"),
    }


async def test_get_ticket(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="BR7UH", name="Eva Nováková")

    assert ticket == Ticket(order="BR7UH", name="Eva Nováková", type="Business")


async def test_get_ticket_ignores_accents(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="BR7UH", name="Jan Novak")

    assert ticket == Ticket(order="BR7UH", name="Jan Novák", type="Business")


async def test_get_ticket_ignores_name_order(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="RCZN9", name="Meikäläinen Maija")

    assert ticket == Ticket(order="RCZN9", name="Maija Meikäläinen", type="Personal")


async def test_get_ticket_returns_none_on_unknown_input(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="ABC01", name="John Doe")

    assert ticket is None


async def test_get_ticket_ignores_unpaid_orders(pretix_mock):
    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)

    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="PFZBT", name="Erika Mustermann")

    assert ticket is None


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
            "/orders": lambda: web.json_response(json.loads(mock_orders_file.read_text())),
        },
        port=port,
        aiohttp_client=aiohttp_client,
        unused_tcp_port_factory=unused_tcp_port_factory,
    )

    pretix_connector = PretixConnector(url=pretix_mock.base_url, token=PRETIX_API_TOKEN)
    await pretix_connector.fetch_pretix_data()

    assert len(pretix_connector.items_by_id) == 5, "Only the first page of '/items' was fetched."


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

    initial_time = datetime.now(tz=timezone.utc)

    # initial fetch should fetch everything
    await pretix_connector.fetch_pretix_data()

    assert len(requests) == 2
    assert requests[0].url.path == "/items"
    assert requests[1].url.path == "/orders"

    # third fetch after >2 minutes should fetch updates
    three_minutes_before = initial_time - timedelta(minutes=3)
    pretix_connector._last_fetch = three_minutes_before

    requests.clear()
    await pretix_connector.fetch_pretix_data()

    assert len(requests) == 2
    assert requests[0].url.path == "/items"
    assert requests[1].url.path == "/orders"
    assert datetime.fromisoformat(requests[1].url.query["modified_since"]) == three_minutes_before
