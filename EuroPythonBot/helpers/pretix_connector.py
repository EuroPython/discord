import os
from http import HTTPStatus
from pathlib import Path
from typing import Dict

import aiohttp
from configuration import Config
from dotenv import load_dotenv
from error import AlreadyRegisteredError, NotFoundError

config = Config()

load_dotenv(Path("__file__").resolve().parent.joinpath(".secrets"))
PRETIX_TOKEN = os.getenv("PRETIX_TOKEN")
HEADERS = {"Authorization": f"Token {PRETIX_TOKEN}"}


def sanitize_string(input_string: str) -> str:
    """Process the name to make it more uniform."""
    return input_string.replace(" ", "").lower()


async def get_id_to_name_map() -> Dict[int, str]:
    url = f"{config.PRETIX_BASE_URL}/items"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            if response.status != HTTPStatus.OK:
                response.raise_for_status()

            data = await response.json()

            id_to_name = {}
            for result in data.get("results"):
                id = result.get("id")
                name = result.get("name").get("en")
                id_to_name[id] = name
                for variation in result.get("variations"):
                    variation_id = variation.get("id")
                    variation_name = variation.get("value").get("en")
                    id_to_name[variation_id] = variation_name
    return id_to_name


async def get_pretix_checkinlists_data():
    id_to_name = await get_id_to_name_map()

    url = f"{config.PRETIX_BASE_URL}/checkinlists/{config.CHECKINLIST_ID}/positions"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            if response.status != HTTPStatus.OK:
                response.raise_for_status()

            data = await response.json()

            orders = {}
            for result in data.get("results"):
                order = result.get("order")
                attendee_name = sanitize_string(result.get("attendee_name"))
                item = result.get("item")
                variation = result.get("variation")

                orders[f"{order}-{attendee_name}"] = "-".join(
                    [id_to_name.get(item, ""), id_to_name.get(variation, "")]
                )
    return orders


REGISTERED_SET = set()


def validate_key(key: str) -> bool:
    if key in REGISTERED_SET:
        raise AlreadyRegisteredError("Ticket already registered")
    return True


async def get_ticket_type(order: str, full_name: str) -> str:
    checkinlist = await get_pretix_checkinlists_data()
    key = f"{order}-{sanitize_string(input_string=full_name)}"
    validate_key(key)
    ticket_type = None
    try:
        ticket_type = checkinlist[key]
        REGISTERED_SET.add(key)
    except KeyError:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.PRETIX_BASE_URL}/checkinlists/{config.CHECKINLIST_ID}/positions",
                headers=HEADERS,
                params={
                    "order": order,
                    "attendee_name": full_name,
                },
            ) as request:
                if request.status == HTTPStatus.OK:
                    ID_TO_NAME = await get_id_to_name_map()

                    data = await request.json()
                    if len(data.get("results")) > 1:
                        result = data.get("results")[0]

                        item = result.get("item")
                        variation = result.get("variation")

                        ticket_type = f"{ID_TO_NAME.get(item)}-{ID_TO_NAME.get(variation)}"
                        REGISTERED_SET.add(key)
                    else:
                        raise NotFoundError("No ticket found")
                else:
                    print(f"Error occurred: Status {request.status}")
    return ticket_type


async def get_roles(name: str, order: str) -> int:
    """Get the role for the user."""
    ticket_type = await get_ticket_type(full_name=name, order=order)

    return config.TICKET_TO_ROLE.get(ticket_type)
