import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv(Path("__file__").absolute().parent.joinpath(".secrets"))

PRETIX_TOKEN = os.getenv("PRETIX_TOKEN")
PRETIX_BASE_URL = (
    "https://pretix.eu/api/v1/organizers/europython/events/ep2023-staging2/"
)


def get_input(info):
    result = info.split(",")
    if result:
        return result[0].strip(), result[1].strip()


async def create_id_to_name_dict():
    headers = {
        "Authorization": f"Token {PRETIX_TOKEN}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(PRETIX_BASE_URL + "items/", headers=headers) as request:
            if request.status == 200:
                data = await request.json()
                id_to_name = {}

                for result in data["results"]:
                    id_value = result["id"]
                    name_value = result["name"]["en"]
                    id_to_name[id_value] = name_value
                return id_to_name
            else:
                print(f"Error occurred: Status {request.status}")
    return dict()


async def get_id_to_checking_list_dict():
    headers = {
        "Authorization": f"Token {PRETIX_TOKEN}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            PRETIX_BASE_URL + "checkinlists", headers=headers
        ) as request:
            if request.status == 200:
                data = await request.json()
                name_to_id = {}

                for result in data["results"]:
                    id_value = result["id"]
                    name_value = result["name"]
                    name_to_id[name_value] = id_value
                return name_to_id
            else:
                print(f"Error occurred: Status {request.status}")
    return dict()


async def get_ticket_type(order, full_name):
    headers = {
        "Authorization": f"Token {PRETIX_TOKEN}",
    }
    checking_list_to_id = await get_id_to_checking_list_dict()
    id_to_name = await create_id_to_name_dict()

    async with aiohttp.ClientSession() as session:
        async with session.get(
            PRETIX_BASE_URL
            + f"checkinlists/{checking_list_to_id['Default']}/positions",
            headers=headers,
            params={
                "order": order,
                "attendee_name": full_name,
            },
        ) as request:
            if request.status == 200:
                data = await request.json()
                return f"You have a {id_to_name[data['results'][0]['item']]} ticket"
            else:
                print(f"Error occurred: Status {request.status}")
    return dict()
