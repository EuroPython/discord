import asyncio
import os
from pathlib import Path
from typing import Dict

import aiohttp
import requests
from dotenv import load_dotenv

import discord

load_dotenv(Path("__file__").resolve().parent.joinpath(".secrets"))
PRETIX_TOKEN = os.getenv("PRETIX_TOKEN")
PRETIX_BASE_URL = "https://pretix.eu/api/v1/organizers/europython/events/ep2023-staging2"
CHECKINLIST_ID = 295151
HEADERS = {"Authorization": f"Token {PRETIX_TOKEN}"}


def sanitize_string(input_string: str) -> str:
    """Process the name to make it more uniform."""
    return input_string.replace(" ", "").lower()


def get_id_to_name_map() -> Dict[int, str]:
    URL = f"{PRETIX_BASE_URL}/items"
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
    URL = f"{PRETIX_BASE_URL}/checkinlists/{CHECKINLIST_ID}/positions"
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


CHECKINNAME = get_pretix_checkinlists_data()


async def get_ticket_type(order: str, full_name: str) -> str:
    key = f"{order}-{sanitize_string(input_string=full_name)}"
    ticket_type = None
    try:
        ticket_type = CHECKINNAME[key]
    except KeyError:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{PRETIX_BASE_URL}/checkinlists/{CHECKINLIST_ID}/positions",
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
                    else:
                        raise Exception("No ticket found")
                else:
                    print(f"Error occurred: Status {request.status}")
    return ticket_type


async def get_role(name: str, order: str) -> str:
    """Get the role for the user."""
    ticket_type = await get_ticket_type(full_name=name, order=order)
    return f"Role for {ticket_type} ticket"


async def assign_role(interaction: discord.Interaction, name: str, order: str) -> None:
    """Assign the role to the user and send a confirmation message."""
    role = await get_role(name=name, order=order)
    await interaction.response.send_message(
        f"Thank you {name}, you are now registered.! ({role})",
        ephemeral=True,
        delete_after=20,
    )


if __name__ == "__main__":
    print(asyncio.run(get_role(name="TODOG Talks No EMu", order="30QNE")))
