from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta
from http import HTTPStatus
from pathlib import Path

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


def sanitize_username(username: str) -> str:
    """Process the name to make it more uniform."""
    return username.replace(" ", "").lower()


def generate_ticket_key(*, order: str, name: str) -> str:
    """Generate a key for identifying ticket registrations."""
    return f"{order}-{sanitize_username(username=name)}"


class PretixConnector:
    def __init__(self):
        self.config = Config()
        load_dotenv(Path(__file__).resolve().parent.parent.parent / ".secrets")

        # https://docs.pretix.eu/en/latest/api/tokenauth.html#using-an-api-token
        self.pretix_api_token = os.getenv("PRETIX_TOKEN")
        self.http_headers = {"Authorization": f"Token {self.pretix_api_token}"}

        self.items_by_id: dict[int, PretixItem | PretixItemVariation] | None = None
        self.ticket_types_by_key: dict[str, str] = {}
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

        _logger.info("Fetching items from pretix")
        self.items_by_id = await self._fetch_pretix_items()

        _logger.info("Fetching orders from pretix")
        self.ticket_types_by_key = await self._fetch_pretix_orders()

        self.last_fetch = datetime.now()

    async def _fetch_pretix_orders(self) -> dict[str, str]:
        orders_as_json = await self._fetch_all_pages(f"{self.config.PRETIX_BASE_URL}/orders")
        orders = [PretixOrder(**order_as_json) for order_as_json in orders_as_json]

        ticket_types_by_key = {}
        for order in orders:
            if not order.is_paid:
                continue

            for position in order.positions:
                item = self.items_by_id[position.item_id]
                item_name = item.names_by_locale["en"]

                if item_name not in self.config.TICKET_TO_ROLE:
                    # item does not grant any Discord roles (e.g. 'T-Shirt')
                    continue

                order_key = generate_ticket_key(order=order.id, name=position.attendee_name)
                ticket_types_by_key[order_key] = item_name
        return ticket_types_by_key

    async def _fetch_pretix_items(self) -> dict[int, PretixItem | PretixItemVariation]:
        """Fetch all items from the Pretix API."""
        items_as_json = await self._fetch_all_pages(f"{self.config.PRETIX_BASE_URL}/items")

        items_by_id = {}
        for item_as_json in items_as_json:
            item = PretixItem(**item_as_json)
            items_by_id[item.id] = item
            for variation in item.variations:
                items_by_id[variation.id] = variation

        return items_by_id

    async def _fetch_all_pages(self, url: str) -> list[dict]:
        """Fetch all pages from a paginated Pretix API endpoint."""
        # https://docs.pretix.eu/en/latest/api/fundamentals.html#pagination
        results = []

        _logger.debug("Fetching all pages from %s", url)
        start = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            next_url: str | None = url
            while next_url is not None:
                _logger.debug("Fetching %s", url)
                async with session.get(next_url, headers=self.http_headers) as response:
                    if response.status != HTTPStatus.OK:
                        response.raise_for_status()

                    data = await response.json()

                results += data["results"]
                next_url = data["next"]
                _logger.debug("Found %d items", data["count"])

            _logger.info(
                "Fetched %d results in %.3f seconds", len(results), time.perf_counter() - start
            )
            return results

    async def _get_ticket_type(self, *, order: str, name: str) -> str:
        """Get a given ticket holder's ticket type."""

        key = generate_ticket_key(order=order, name=name)

        if key in self.registered_users:
            raise AlreadyRegisteredError(f"Ticket already registered: {key=}")

        if key not in self.ticket_types_by_key:
            if datetime.now() - self.last_fetch < timedelta(minutes=15):
                await self.fetch_pretix_data()

        if key in self.ticket_types_by_key:
            return self.ticket_types_by_key[key]

        raise NotFoundError(f"No ticket found: {order=}, {name=}")

    async def mark_as_registered(self, *, order: str, name: str) -> None:
        """Mark a ticket holder as registered."""
        key = generate_ticket_key(order=order, name=name)

        self.registered_users.add(key)
        async with aiofiles.open(self.registered_file, mode="a") as f:
            await f.write(f"{key}\n")

    async def get_roles(self, *, order: str, name: str) -> list[int]:
        """Get the role IDs for a given ticket holder."""

        ticket_type = await self._get_ticket_type(order=order, name=name)
        return self.config.TICKET_TO_ROLE.get(ticket_type)
