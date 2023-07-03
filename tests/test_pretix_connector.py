import json
from pathlib import Path

import pytest
from aiohttp import web
from configuration import Config
from helpers.pretix_connector import get_pretix_checkinlists_data, get_roles

config = Config()


async def items(request):
    with open(Path("tests", "mock_pretix_items.json")) as json_file:
        mock_response = json.load(json_file)
    return web.json_response(mock_response)


async def positions(request):
    with open(Path("tests", "mock_pretix_checkinglists_list_positions.json")) as json_file:
        mock_response = json.load(json_file)
    return web.json_response(mock_response)


@pytest.mark.asyncio
async def test_get_pretix_checkinlists_data(aiohttp_client, event_loop):
    expected_response = {
        "90LKW-dogtbd": "Personal-Conference",
        "M09CT-order2dog": "Business-Conference",
        "M09CT-order3dog": "Business-Conference",
        "M09CT-order4dog": "Business-Conference",
        "M09CT-order5dog": "Business-Conference",
        "M09CT-order6dog": "Business-Conference",
        "C0MV7-raquelindividual": "Business-Conference",
        "G0CFM-raquelindividual": "Business-Conference",
        "90LKW-tbdtbd": "Business-Conference",
        "RCZN9-todoggodot": "Presenter-Speaker",
        "30QNE-todogtalksnoemu": "Presenter-Speaker",
    }

    app = web.Application()
    app.router.add_get("/items", items)
    app.router.add_get(f"/checkinlists/{config.CHECKINLIST_ID}/positions", positions)

    client = await aiohttp_client(app)

    # Replace the actual PRETIX_BASE_URL with the mock server URL
    base_url_backup = config.PRETIX_BASE_URL
    config.PRETIX_BASE_URL = str(client.make_url(""))

    data = await get_pretix_checkinlists_data()

    config.PRETIX_BASE_URL = base_url_backup

    assert expected_response == data


@pytest.mark.asyncio
async def test_get_roles(aiohttp_client, event_loop):
    test_data = [
        (
            "TODOG GODOT",
            "RCZN9",
            config.TICKET_TO_ROLE["Presenter-Speaker"],
        ),
        (
            "order 6 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
        (
            "TBD TBD",
            "90LKW",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
        (
            "TODOG Talks No EMu",
            "30QNE",
            config.TICKET_TO_ROLE["Presenter-Speaker"],
        ),
        (
            "Raquel Individual",
            "C0MV7",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
        (
            "Raquel Individual",
            "G0CFM",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
        (
            "order 2 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
        (
            "Dog TBD",
            "90LKW",
            config.TICKET_TO_ROLE["Personal-Conference"],
        ),
        (
            "order 3 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
        (
            "order 4 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
        (
            "order 5 dog",
            "M09CT",
            config.TICKET_TO_ROLE["Business-Conference"],
        ),
    ]

    app = web.Application()
    app.router.add_get("/items", items)
    app.router.add_get(f"/checkinlists/{config.CHECKINLIST_ID}/positions", positions)

    client = await aiohttp_client(app)

    base_url_backup = config.PRETIX_BASE_URL
    config.PRETIX_BASE_URL = str(client.make_url(""))

    for name, order, role_ids in test_data:
        roles = await get_roles(name=name, order=order)
        assert roles == role_ids

    config.PRETIX_BASE_URL = base_url_backup
