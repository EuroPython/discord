import json
from pathlib import Path

import pytest
from aiohttp import web

from configuration import Config
from helpers.pretix_connector import PretixConnector, generate_ticket_key

config = Config()


async def items(request):
    with open(Path(__file__).parent / "mock_pretix_items.json") as json_file:
        mock_response = json.load(json_file)
    return web.json_response(mock_response)


async def orders(request):
    with open(Path(__file__).parent / "mock_pretix_orders.json") as json_file:
        mock_response = json.load(json_file)
    return web.json_response(mock_response)


@pytest.mark.asyncio
async def test_get_pretix_orders_data(aiohttp_client, monkeypatch):
    expected_response = {
        "90LKW-dogtbd": "Personal",
        "90LKW-cattbd": "Remote Ticket",
        "N0XE9-thepetkgmailcomthepetkgmailcom": "Remote Ticket",
        "M09CT-order2dog": "Business",
        "M09CT-order3dog": "Business",
        "M09CT-order4dog": "Business",
        "M09CT-order5dog": "Business",
        "M09CT-order6dog": "Business",
        "C0MV7-raquelindividual": "Business",
        "G0CFM-raquelindividual": "Business",
        "90LKW-tbdtbd": "Business",
        "RCZN9-todoggodot": "Presenter",
        "30QNE-todogtalksnoemu": "Presenter",
    }

    app = web.Application()
    app.router.add_get("/items", items)
    app.router.add_get("/orders", orders)

    client = await aiohttp_client(app)

    # Replace the actual PRETIX_BASE_URL with the mock server URL
    monkeypatch.setattr(config, "PRETIX_BASE_URL", str(client.make_url("")))

    pretix_connector = PretixConnector()

    await pretix_connector.fetch_pretix_data()

    assert expected_response == pretix_connector.ticket_types_by_key


@pytest.mark.asyncio
async def test_get_roles(aiohttp_client, monkeypatch):
    # (name, order, roles)
    test_data = [
        ("TODOG GODOT", "RCZN9", config.TICKET_TO_ROLE["Presenter"]),
        ("order 6 dog", "M09CT", config.TICKET_TO_ROLE["Business"]),
        ("TBD TBD", "90LKW", config.TICKET_TO_ROLE["Business"]),
        ("TODOG Talks No EMu", "30QNE", config.TICKET_TO_ROLE["Presenter"]),
        ("Raquel Individual", "C0MV7", config.TICKET_TO_ROLE["Business"]),
        ("Raquel Individual", "G0CFM", config.TICKET_TO_ROLE["Business"]),
        ("order 2 dog", "M09CT", config.TICKET_TO_ROLE["Business"]),
        ("Dog TBD", "90LKW", config.TICKET_TO_ROLE["Personal"]),
        ("order 3 dog", "M09CT", config.TICKET_TO_ROLE["Business"]),
        ("order 4 dog", "M09CT", config.TICKET_TO_ROLE["Business"]),
        ("order 5 dog", "M09CT", config.TICKET_TO_ROLE["Business"]),
    ]

    app = web.Application()
    app.router.add_get("/items", items)
    app.router.add_get("/orders", orders)

    client = await aiohttp_client(app)

    # Replace the actual PRETIX_BASE_URL with the mock server URL
    monkeypatch.setattr(config, "PRETIX_BASE_URL", str(client.make_url("")))

    pretix_connector = PretixConnector()

    await pretix_connector.fetch_pretix_data()

    for name, order, role_ids in test_data:
        roles = await pretix_connector.get_roles(name=name, order=order)
        assert roles == role_ids


@pytest.mark.parametrize(
    ("name", "result"),
    [
        ("Karel Čapek", "karelcapek"),
        ("Shin Kyung-sook", "shinkyungsook"),
        ("Ch'oe Yun", "choeyun"),
        ("Æmilia Lanyer", "aemilialanyer"),
        ("name@example.com", "nameexamplecom"),
    ],
)
def test_name_normalization(name, result):
    assert generate_ticket_key(order="ABC01", name=name) == f"ABC01-{result}"


@pytest.mark.parametrize(
    ("name_in_pretix", "name"),
    [
        ("Jane Doe", "Jane Doe"),
        ("Ki-moon Ban", "Ban Ki-moon"),
    ],
)
async def test_name_permutations(name_in_pretix, name):
    pretix_connector = PretixConnector()

    key = generate_ticket_key(order="ABC01", name=name_in_pretix)
    pretix_connector.ticket_types_by_key[key] = "Business"

    roles = await pretix_connector.get_roles(order="ABC01", name=name)
    assert len(roles) > 0
