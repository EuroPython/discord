import json
from pathlib import Path

import pytest
from aiohttp import web
from configuration import Config
from helpers.pretix_connector import PretixOrder

config = Config()
order_ins = PretixOrder()


async def items(request):
    with open(Path("tests", "mock_pretix_items.json")) as json_file:
        mock_response = json.load(json_file)
    return web.json_response(mock_response)


async def positions(request):
    with open(Path("tests", "mock_pretix_orders.json")) as json_file:
        mock_response = json.load(json_file)
    return web.json_response(mock_response)


@pytest.mark.asyncio
async def test_get_pretix_orders_data(aiohttp_client, event_loop):
    expected_response = {
        "90LKW-dogtbd": "Personal",
        "90LKW-cattbd": "Remote Ticket",
        "N0XE9-thepetk@gmail.comthepetk@gmail.com": "Remote Ticket",
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
    app.router.add_get("/orders", positions)

    client = await aiohttp_client(app)

    # Replace the actual PRETIX_BASE_URL with the mock server URL
    base_url_backup = config.PRETIX_BASE_URL
    config.PRETIX_BASE_URL = str(client.make_url(""))

    await order_ins.fetch_data()

    config.PRETIX_BASE_URL = base_url_backup

    assert expected_response == order_ins.orders


@pytest.mark.asyncio
async def test_get_roles(aiohttp_client, event_loop):
    test_data = [
        (
            "TODOG GODOT",
            "RCZN9",
            config.TICKET_TO_ROLE["Presenter"],
        ),
        (
            "order 6 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business"],
        ),
        (
            "TBD TBD",
            "90LKW",
            config.TICKET_TO_ROLE["Business"],
        ),
        (
            "TODOG Talks No EMu",
            "30QNE",
            config.TICKET_TO_ROLE["Presenter"],
        ),
        (
            "Raquel Individual",
            "C0MV7",
            config.TICKET_TO_ROLE["Business"],
        ),
        (
            "Raquel Individual",
            "G0CFM",
            config.TICKET_TO_ROLE["Business"],
        ),
        (
            "order 2 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business"],
        ),
        (
            "Dog TBD",
            "90LKW",
            config.TICKET_TO_ROLE["Personal"],
        ),
        (
            "order 3 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business"],
        ),
        (
            "order 4 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business"],
        ),
        (
            "order 5 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business"],
        ),
    ]

    app = web.Application()
    app.router.add_get("/items", items)
    app.router.add_get("/orders", positions)

    client = await aiohttp_client(app)

    base_url_backup = config.PRETIX_BASE_URL
    config.PRETIX_BASE_URL = str(client.make_url(""))

    await order_ins.fetch_data()

    for name, order, role_ids in test_data:
        roles = await order_ins.get_roles(name=name, order=order)
        assert roles == role_ids

    config.PRETIX_BASE_URL = base_url_backup

def test_save_load_register(tmp_path):
    test_data = set(['12345', '67890'])
    order_ins.registered_file = tmp_path / "test.txt"
    order_ins.REGISTERED_SET = test_data
    order_ins.save_registered()
    order_ins.REGISTERED_SET = set()
    order_ins.load_registered()
    assert order_ins.REGISTERED_SET == test_data
