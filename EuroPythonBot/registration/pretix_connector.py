from __future__ import annotations

import asyncio
import itertools
import logging
import time
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import aiohttp

from registration.pretix_api_response_models import PretixItem, PretixItemVariation, PretixOrder
from registration.ticket import Ticket, generate_ticket_key

_logger = logging.getLogger(f"bot.{__name__}")


class PretixConnector:
    def __init__(self, *, url: str, token: str):
        self._pretix_api_url = url

        # https://docs.pretix.eu/en/latest/api/tokenauth.html#using-an-api-token
        self._http_headers = {"Authorization": f"Token {token}"}

        self._fetch_lock = asyncio.Lock()

        self.items_by_id: dict[int, PretixItem | PretixItemVariation] = {}
        self.tickets_by_key: dict[str, Ticket] = {}
        self._last_fetch: datetime | None = None

    async def fetch_pretix_data(self) -> None:
        """Fetch order and item data from the Pretix API and cache it."""
        # if called during an ongoing fetch, the caller waits until the fetch is done...
        async with self._fetch_lock:
            # ... but does not trigger a second fetch
            now = datetime.now(tz=timezone.utc)
            if self._last_fetch and now - self._last_fetch < timedelta(minutes=2):
                _logger.info(f"Skipping pretix fetch (last fetch was at {self._last_fetch})")
                return

            await self._fetch_pretix_items()
            await self._fetch_pretix_orders()
            self._last_fetch = now

    async def _fetch_pretix_orders(self) -> None:
        # initially fetch all orders, then only fetch updates
        params = {"testmode": "false"}
        if len(self.tickets_by_key) == 0:
            _logger.info("Fetching all pretix orders")
        else:
            _logger.info("Fetching pretix orders since %s", self._last_fetch)
            params["modified_since"] = self._last_fetch.isoformat()

        orders_as_json = await self._fetch_all_pages(
            f"{self._pretix_api_url}/orders",
            params=params,
        )

        for order_as_json in orders_as_json:
            order = PretixOrder(**order_as_json)
            if not order.is_paid:
                continue

            for position in order.positions:
                item = self.items_by_id[position.item_id]
                item_name = item.names_by_locale["en"]

                ticket = Ticket(order=order.id, name=position.attendee_name, type=item_name)
                self.tickets_by_key[ticket.key] = ticket

    async def _fetch_pretix_items(self) -> None:
        """Fetch all items from the Pretix API."""
        items_as_json = await self._fetch_all_pages(f"{self._pretix_api_url}/items")

        for item_as_json in items_as_json:
            item = PretixItem(**item_as_json)
            self.items_by_id[item.id] = item
            for variation in item.variations:
                self.items_by_id[variation.id] = variation

    async def _fetch_all_pages(self, url: str, params: dict[str, str] | None = None) -> list[dict]:
        """Fetch all pages from a paginated Pretix API endpoint."""
        # https://docs.pretix.eu/en/latest/api/fundamentals.html#pagination
        results = []

        _logger.debug("Fetching all pages from %s (params: %r)", url, params)
        start = time.perf_counter()
        async with aiohttp.ClientSession(headers=self._http_headers) as session:
            next_url: str | None = url
            while next_url is not None:
                _logger.debug("Fetching %s", url)

                # only send params on initial request
                if next_url != url:
                    params = None

                async with session.get(next_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                page_results = data["results"]
                results += page_results
                next_url = data["next"]
                _logger.debug("Found %d items", len(page_results))

            _logger.info(
                "Fetched %d results in %.3f seconds", len(results), time.perf_counter() - start
            )
            return results

    def get_ticket(self, *, order: str, name: str) -> Ticket | None:
        """Get the ticket for a given order ID and name, or None if none was found."""
        # try different name orders (e.g. family name first vs last)
        # limit number of possible permutations to test to prevent abuse
        max_name_components = 5
        name_parts = name.split(maxsplit=max_name_components - 1)
        for permutation in itertools.permutations(name_parts):
            possible_name = " ".join(permutation)

            key = generate_ticket_key(order=order, name=possible_name)

            if key in self.tickets_by_key:
                return self.tickets_by_key[key]

        return None
