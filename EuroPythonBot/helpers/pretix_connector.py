import os
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from time import time
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


async def fetch(url, session):
    async with session.get(url, headers=HEADERS) as response:
        return await response.json()


async def fetch_all(url):
    async with aiohttp.ClientSession() as session:
        results = []
        while url:
            data = await fetch(url, session)
            results += data["results"]
            url = data["next"]
        return results


def flatten_concatenation(matrix):
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list


async def get_pretix_orders_data():
    print(f"{datetime.now()} INFO: Fetching IDs names from pretix")
    id_to_name = await get_id_to_name_map()
    print(f"{datetime.now()} INFO: Done fetching IDs names from pretix")

    url = f"{config.PRETIX_BASE_URL}/orders"

    print(f"{datetime.now()} INFO: Fetching orders from pretix")
    time_start = time()
    results = await fetch_all(url)
    print(f"{datetime.now()} INFO: Fetched {len(results)} orders in {time() - time_start} seconds")

    orders = {}
    for position in flatten_concatenation(
        [result.get("positions") for result in results if result.get("status") == "p"]
    ):
        item = position.get("item")
        if id_to_name.get(item) in ["T-shirt (free)", "Childcare (Free)", "Livestream Only"]:
            continue
        order = position.get("order")
        print(f"{item=} {id_to_name.get(item)=} {order=}")
        attendee_name = sanitize_string(position.get("attendee_name"))
        print(f"{attendee_name=}")

        orders[f"{order}-{attendee_name}"] = id_to_name.get(item)
    return orders


REGISTERED_SET = set()


def validate_key(key: str) -> bool:
    if key in REGISTERED_SET:
        raise AlreadyRegisteredError(f"Ticket already registered - id: {key}")
    return True


async def get_ticket_type(order: str, full_name: str) -> str:
    orders = await get_pretix_orders_data()
    key = f"{order}-{sanitize_string(input_string=full_name)}"
    validate_key(key)
    ticket_type = None
    try:
        ticket_type = orders[key]
        REGISTERED_SET.add(key)
    except KeyError:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.PRETIX_BASE_URL}/orders",
                headers=HEADERS,
                params={
                    "code": order,
                    "search": full_name,
                },
            ) as request:
                if request.status == HTTPStatus.OK:
                    id_to_name = await get_id_to_name_map()

                    data = await request.json()
                    if len(data.get("results")) > 1:
                        result = data.get("results")[0]
                        if result.get("status") != "p":
                            raise Exception("Order not paid")
                        item = result.get("item")
                        variation = result.get("variation")

                        ticket_type = f"{id_to_name.get(item)}-{id_to_name.get(variation)}"
                        REGISTERED_SET.add(key)
                    else:
                        raise NotFoundError(f"No ticket found - inputs: {order=}, {full_name=}")
                else:
                    print(f"Error occurred: Status {request.status}")
    return ticket_type


async def get_roles(name: str, order: str) -> int:
    """Get the role for the user."""
    ticket_type = await get_ticket_type(full_name=name, order=order)

    return config.TICKET_TO_ROLE.get(ticket_type)
