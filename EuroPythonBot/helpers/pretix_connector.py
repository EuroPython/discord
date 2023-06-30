import os
from pathlib import Path
from typing import Dict

import aiohttp
import requests
from configuration import Config
from dotenv import load_dotenv

config = Config()

load_dotenv(Path("__file__").resolve().parent.joinpath(".secrets"))
PRETIX_TOKEN = os.getenv("PRETIX_TOKEN")
HEADERS = {"Authorization": f"Token {PRETIX_TOKEN}"}


def sanitize_string(input_string: str) -> str:
    """Process the name to make it more uniform."""
    return input_string.replace(" ", "").lower()


def get_id_to_name_map() -> Dict[int, str]:
    URL = f"{config.PRETIX_BASE_URL}/items"
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()

    id_to_name = {}
    for result in response.json().get("results"):
        id = result.get("id")
        name = result.get("name").get("en")
        id_to_name[id] = name
        for variation in result.get("variations"):
            variation_id = variation.get("id")
            variation_name = variation.get("value").get("en")
            id_to_name[variation_id] = variation_name
    return id_to_name


ID_TO_NAME = get_id_to_name_map()


def get_pretix_checkinlists_data():
    URL = f"{config.PRETIX_BASE_URL}/checkinlists/{config.CHECKINLIST_ID}/positions"
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()

    orders = {}
    for result in response.json().get("results"):
        order = result.get("order")
        attendee_name = sanitize_string(result.get("attendee_name").replace(" ", ""))
        item = result.get("item")
        variation = result.get("variation")

        orders[f"{order}-{attendee_name}"] = "-".join([ID_TO_NAME[item], ID_TO_NAME[variation]])
    return orders


CHECKINLISTS = get_pretix_checkinlists_data()
REGISTERED_SET = set()


def validate_key(key: str) -> bool:
    if key in REGISTERED_SET:
        raise Exception("Key already registered")
    return True


async def get_ticket_type(order: str, full_name: str) -> str:
    key = f"{order}-{sanitize_string(input_string=full_name)}"
    validate_key(key)
    ticket_type = None
    try:
        ticket_type = CHECKINLISTS[key]
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
                if request.status == 200:
                    data = await request.json()
                    if len(data.get("results")) > 1:
                        result = data.get("results")[0]

                        item = result.get("item")
                        variation = result.get("variation")

                        ticket_type = f"{ID_TO_NAME.get(item)}-{ID_TO_NAME.get(variation)}"
                        REGISTERED_SET.add(key)
                    else:
                        raise Exception("No ticket found")
                else:
                    print(f"Error occurred: Status {request.status}")
    return ticket_type


async def get_role(name: str, order: str) -> int:
    """Get the role for the user."""
    ticket_type = await get_ticket_type(full_name=name, order=order)
    return config.TICKET_TO_ROLE.get(ticket_type)
