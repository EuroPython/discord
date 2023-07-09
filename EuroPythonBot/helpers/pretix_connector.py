import os
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from time import time
from typing import Dict, List

import aiohttp
from configuration import Config, Singleton
from dotenv import load_dotenv
from error import AlreadyRegisteredError, NotFoundError


def sanitize_string(input_string: str) -> str:
    """Process the name to make it more uniform."""
    return input_string.replace(" ", "").lower()


class PretixOrder(metaclass=Singleton):
    def __init__(self):
        self.config = Config()
        load_dotenv(Path("__file__").resolve().parent.joinpath(".secrets"))

        PRETIX_TOKEN = os.getenv("PRETIX_TOKEN")
        self.HEADERS = {"Authorization": f"Token {PRETIX_TOKEN}"}

        self.id_to_name = None
        self.orders = {}
        self.last_fetch = None

        self.registered_file = getattr(self.config, "REGISTERED_LOG_FILE", "./registered_log.txt")
        self.REGISTERED_SET = set()

    def load_registered(self):
        try:
            f = open(self.registered_file, "r")
            registered = [reg.strip() for reg in f.readlines()]
            self.REGISTERED_SET = set(registered)
            f.close()
        except Exception as err:
            print(f"Cannot load registered data due to {err}, starting from scratch.")

    def save_registered(self):
        if self.REGISTERED_SET:
            print("Saving registered tickets...")
            f = open(self.registered_file, "w")
            for item in self.REGISTERED_SET:
                f.write(f"{item}\n")
            f.close()

    async def fetch_data(self) -> None:
        """Fetch data from Pretix, store id_to_name mapping and formated orders internally"""

        print(f"{datetime.now()} INFO: Fetching IDs names from pretix")
        self.id_to_name = await self._get_id_to_name_map()
        print(f"{datetime.now()} INFO: Done fetching IDs names from pretix")

        print(f"{datetime.now()} INFO: Fetching orders from pretix")
        time_start = time()
        results = await self._fetch_all(f"{self.config.PRETIX_BASE_URL}/orders")
        print(
            f"{datetime.now()} INFO: Fetched {len(results)} orders in {time() - time_start} seconds"
        )

        def flatten_concatenation(matrix):
            flat_list = []
            for row in matrix:
                flat_list += row
            return flat_list

        orders = {}
        for position in flatten_concatenation(
            [result.get("positions") for result in results if result.get("status") == "p"]
        ):
            item = position.get("item")
            if self.id_to_name.get(item) in [
                "T-shirt (free)",
                "Childcare (Free)",
                "Livestream Only",
            ]:
                continue
            order = position.get("order")
            attendee_name = sanitize_string(position.get("attendee_name"))

            orders[f"{order}-{attendee_name}"] = self.id_to_name.get(item)

        self.orders = orders
        self.last_fetch = datetime.now()

    async def _get_id_to_name_map(self) -> Dict[int, str]:
        url = f"{self.config.PRETIX_BASE_URL}/items"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.HEADERS) as response:
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

    async def _fetch(self, url, session):
        async with session.get(url, headers=self.HEADERS) as response:
            return await response.json()

    async def _fetch_all(self, url):
        async with aiohttp.ClientSession() as session:
            results = []
            while url:
                data = await self._fetch(url, session)
                results += data.get("results")
                url = data.get("next")
            return results

    async def get_ticket_type(self, order: str, full_name: str) -> str:
        """With user input `order` and `full_name`, check for their ticket type"""

        key = f"{order}-{sanitize_string(input_string=full_name)}"
        self.validate_key(key)
        ticket_type = None
        try:
            ticket_type = self.orders[key]
            self.REGISTERED_SET.add(key)
        except KeyError:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.PRETIX_BASE_URL}/orders",
                    headers=self.HEADERS,
                    params={
                        "code": order,
                        "search": full_name,
                    },
                ) as request:
                    if request.status == HTTPStatus.OK:
                        data = await request.json()
                        if len(data.get("results")) > 1:
                            result = data.get("results")[0]
                            if result.get("status") != "p":
                                raise Exception("Order not paid")
                            item = result.get("item")
                            variation = result.get("variation")

                            ticket_type = (
                                f"{self.id_to_name.get(item)}-{self.id_to_name.get(variation)}"
                            )
                            self.REGISTERED_SET.add(key)
                        else:
                            raise NotFoundError(f"No ticket found - inputs: {order=}, {full_name=}")
                    else:
                        print(f"Error occurred: Status {request.status}")
        return ticket_type

    async def get_roles(self, name: str, order: str) -> List[int]:
        ticket_type = await self.get_ticket_type(full_name=name, order=order)
        return self.config.TICKET_TO_ROLE.get(ticket_type)

    def validate_key(self, key: str) -> bool:
        if key in self.REGISTERED_SET:
            raise AlreadyRegisteredError(f"Ticket already registered - id: {key}")
        return True
