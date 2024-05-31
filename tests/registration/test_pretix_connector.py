import json
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

EXPECTED_PRETIX_API_TOKEN = "MY_PRETIX_API_TOKEN"


@pytest.fixture()
async def pretix_connector(aiohttp_client) -> PretixConnector:
    async def items(request: Request) -> Response:
        if request.headers.get("Authorization") != f"Token {EXPECTED_PRETIX_API_TOKEN}":
            return web.json_response("Missing or wrong Authorization header", status=401)
        return web.json_response(json.loads(mock_items_file.read_text()))

    async def orders(request: Request) -> Response:
        if request.headers.get("Authorization") != f"Token {EXPECTED_PRETIX_API_TOKEN}":
            return web.json_response("Missing or wrong Authorization header", status=401)
        return web.json_response(json.loads(mock_orders_file.read_text()))

    app = web.Application()
    app.router.add_get("/items", items)
    app.router.add_get("/orders", orders)

    client: TestClient = await aiohttp_client(app)

    return PretixConnector(url=str(client.make_url("")), token=EXPECTED_PRETIX_API_TOKEN)


@pytest.mark.asyncio
async def test_pretix_items(pretix_connector):
    await pretix_connector.fetch_pretix_data()

    items_by_id = pretix_connector.items_by_id

    assert len(items_by_id) == 5

    assert items_by_id[339041].names_by_locale["en"] == "Business"
    assert items_by_id[163246].names_by_locale["en"] == "Conference"
    assert items_by_id[163247].names_by_locale["en"] == "Tutorials"
    assert items_by_id[339042].names_by_locale["en"] == "Personal"
    assert items_by_id[163253].names_by_locale["en"] == "Combined (Conference + Tutorials)"


@pytest.mark.asyncio
async def test_pretix_orders(pretix_connector):
    await pretix_connector.fetch_pretix_data()

    assert pretix_connector.tickets_by_key == {
        "BR7UH-evanovakova": Ticket(order="BR7UH", name="Eva Nováková", type="Business"),
        "BR7UH-jannovak": Ticket(order="BR7UH", name="Jan Novák", type="Business"),
        "RCZN9-maijameikalainen": Ticket(order="RCZN9", name="Maija Meikäläinen", type="Personal"),
    }


async def test_get_ticket(pretix_connector):
    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="BR7UH", name="Eva Nováková")

    assert ticket == Ticket(order="BR7UH", name="Eva Nováková", type="Business")


async def test_get_ticket_ignores_accents(pretix_connector):
    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="BR7UH", name="Jan Novak")

    assert ticket == Ticket(order="BR7UH", name="Jan Novák", type="Business")


async def test_get_ticket_ignores_name_order(pretix_connector):
    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="RCZN9", name="Meikäläinen Maija")

    assert ticket == Ticket(order="RCZN9", name="Maija Meikäläinen", type="Personal")


async def test_get_ticket_returns_none_on_unknown_input(pretix_connector):
    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="ABC01", name="John Doe")

    assert ticket is None


async def test_get_ticket_ignores_unpaid_orders(pretix_connector):
    await pretix_connector.fetch_pretix_data()

    ticket = pretix_connector.get_ticket(order="PFZBT", name="Erika Mustermann")

    assert ticket is None


async def test_pagination(aiohttp_client, aiohttp_unused_port):
    port = aiohttp_unused_port()
    base_url = f"http://127.0.0.1:{port}"

    async def items(request: Request) -> Response:
        return web.json_response(
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
        )

    async def items2(request: Request) -> Response:
        return web.json_response(
            {
                "next": None,
                "results": [
                    {
                        "id": 339042,
                        "name": {"en": "Personal"},
                        "variations": [
                            {"id": 163253, "value": {"en": "Combined (Conference + Tutorials)"}},
                        ],
                    }
                ],
            }
        )

    async def orders(request: Request) -> Response:
        return web.json_response(json.loads(mock_orders_file.read_text()))

    app = web.Application()
    app.router.add_get("/items", items)
    app.router.add_get("/items2", items2)
    app.router.add_get("/orders", orders)

    server = TestServer(app, port=port)
    await aiohttp_client(server)  # start server

    pretix_connector = PretixConnector(url=base_url, token=EXPECTED_PRETIX_API_TOKEN)
    await pretix_connector.fetch_pretix_data()

    assert len(pretix_connector.items_by_id) == 5, "Only the first page of '/items' was fetched."
