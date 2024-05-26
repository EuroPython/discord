from __future__ import annotations

import itertools
import logging
import os
from datetime import datetime, timedelta
from http import HTTPStatus
from pathlib import Path
from time import time

import aiofiles
import aiohttp
import pydantic
from dotenv import load_dotenv

from configuration import Config
from error import AlreadyRegisteredError, NotFoundError

_logger = logging.getLogger(f"bot.{__name__}")


class PretixItem(pydantic.BaseModel):
    """Item which can be ordered, e.g. 'Business', 'Personal', 'Education'."""

    # https://docs.pretix.eu/en/latest/api/resources/items.html
    id: int
    names_by_locale: dict[str, str] = pydantic.Field(alias="name")
    variations: list[PretixItemVariation]


class PretixItemVariation(pydantic.BaseModel):
    """Variation of item, e.g. 'Conference', 'Tutorial', 'Volunteer'."""

    # https://docs.pretix.eu/en/latest/api/resources/item_variations.html
    id: int
    names_by_locale: dict[str, str] = pydantic.Field(alias="value")


class PretixOrder(pydantic.BaseModel):
    """Order containing one or more positions."""

    # https://docs.pretix.eu/en/latest/api/resources/orders.html#order-resource
    id: str = pydantic.Field(alias="code")
    status: str
    positions: list[PretixOrderPosition]

    @property
    def is_paid(self) -> bool:
        # n: pending, p: paid, e: expired, c: canceled
        return self.status == "p"


class PretixOrderPosition(pydantic.BaseModel):
    """Ordered position, e.g. a ticket or a T-shirt"""

    # https://docs.pretix.eu/en/latest/api/resources/orders.html#order-position-resource
    order_id: str = pydantic.Field(alias="order")
    attendee_name: str | None
    item_id: int = pydantic.Field(alias="item")


def sanitize_string(input_string: str) -> str:
    """Process the name to make it more uniform."""
    return input_string.replace(" ", "").lower()


def generate_ticket_key(*, order: str, name: str) -> str:
    """Generate a key for identifying ticket registrations."""
    return f"{order}-{sanitize_string(input_string=name)}"


class PretixConnector:
    def __init__(self):
        self.config = Config()
        load_dotenv(Path(__file__).resolve().parent.parent.parent / ".secrets")

        # https://docs.pretix.eu/en/latest/api/tokenauth.html#using-an-api-token
        self.pretix_api_token = os.getenv("PRETIX_TOKEN")
        self.http_headers = {"Authorization": f"Token {self.pretix_api_token}"}

        self.item_id_to_name: dict[int, str] | None = None
        self.orders: dict[str, str | None] = {}
        self.last_fetch: datetime | None = None

        self.registered_file = getattr(self.config, "REGISTERED_LOG_FILE", "./registered_log.txt")
        self.registered_users = set()

    async def load_registered(self) -> None:
        """Load previously registered participants from the log file."""
        try:
            async with aiofiles.open(self.registered_file) as f:
                lines = await f.readlines()
                self.registered_users = {line.strip() for line in lines}
        except FileNotFoundError:
            _logger.warning(
                f"Cannot load registered data, starting from scratch "
                f"({self.registered_file} does not exist)"
            )
        except Exception:
            _logger.exception("Cannot load registered data, starting from scratch. Error:")

    async def fetch_pretix_data(self) -> None:
        """Fetch order and item data from the Pretix API and cache it."""

        _logger.info("Fetching IDs names from pretix")
        self.item_id_to_name = await self._fetch_pretix_items()
        _logger.info("Done fetching IDs names from pretix")

        _logger.info("Fetching orders from pretix")
        time_start = time()
        results_json = await self._fetch_pretix_orders(f"{self.config.PRETIX_BASE_URL}/orders")
        results = [PretixOrder(**result) for result in results_json]
        _logger.info("Fetched %d orders in %.3f seconds", len(results), time() - time_start)

        orders = {}
        for position in itertools.chain(
            *[result.positions for result in results if result.is_paid]
        ):
            if self.item_id_to_name.get(position.item_id) in [
                "T-shirt (free)",
                "Childcare (Free)",
                "Livestream Only",
            ]:
                continue
            attendee_name = sanitize_string(position.attendee_name)

            orders[f"{position.order_id}-{attendee_name}"] = self.item_id_to_name.get(
                position.item_id
            )

        self.orders = orders
        self.last_fetch = datetime.now()

    async def _fetch_pretix_items(self) -> dict[int, str]:
        """Fetch all items from the Pretix API."""
        async with aiohttp.ClientSession(headers=self.http_headers) as session:
            async with session.get(f"{self.config.PRETIX_BASE_URL}/items") as response:
                if response.status != HTTPStatus.OK:
                    response.raise_for_status()

                data = await response.json()

                id_to_name = {}
                for result in data.get("results"):
                    item = PretixItem(**result)
                    id_to_name[item.id] = item.names_by_locale["en"]
                    for variation in item.variations:
                        id_to_name[variation.id] = variation.names_by_locale["en"]

        return id_to_name

    async def _fetch_pretix_orders(self, url: str):
        """Fetch all orders from the Pretix API."""
        async with aiohttp.ClientSession(headers=self.http_headers) as session:
            results = []

            next_url: str | None = url
            while next_url is not None:
                async with session.get(next_url, headers=self.http_headers) as response:
                    if response.status != HTTPStatus.OK:
                        response.raise_for_status()

                    data = await response.json()

                results += data.get("results")
                next_url = data.get("next")
            return results

    async def _get_ticket_type(self, *, order: str, name: str) -> str:
        """Get a given ticket holder's ticket type."""

        key = generate_ticket_key(order=order, name=name)

        if key in self.registered_users:
            raise AlreadyRegisteredError(f"Ticket already registered: {key=}")

        if key not in self.orders:
            if datetime.now() - self.last_fetch < timedelta(minutes=15):
                await self.fetch_pretix_data()

        if key in self.orders:
            return self.orders[key]

        raise NotFoundError(f"No ticket found: {order=}, {name=}")

    async def mark_as_registered(self, *, order: str, name: str) -> None:
        """Mark a ticket holder as registered."""
        key = generate_ticket_key(order=order, name=name)

        self.registered_users.add(key)
        async with aiofiles.open(self.registered_file, mode="a") as f:
            await f.write(f"{key}\n")

    async def get_roles(self, name: str, order: str) -> list[int]:
        """Get the role IDs for a given ticket holder."""

        ticket_type = await self._get_ticket_type(order=order, name=name)
        return self.config.TICKET_TO_ROLE.get(ticket_type)
