"""Ticket API connector for ticket validation."""

from __future__ import annotations

import logging
from http import HTTPStatus
from pathlib import Path
from time import time

import aiofiles
import aiohttp
from discord.ext import tasks
from dotenv import load_dotenv

from discord_bot.configuration import Config, Singleton
from discord_bot.error import AlreadyRegisteredError, NotFoundError

_logger = logging.getLogger(f"bot.{__name__}")


def sanitize_string(input_string: str) -> str:
    """Process the name to make it more uniform."""
    return input_string.replace(" ", "").lower()


class TicketOrder(metaclass=Singleton):
    """Ticket API connector for ticket validation."""

    def __init__(self) -> None:
        """Initialize the TicketOrder class."""
        self.config = Config()
        load_dotenv(Path(__file__).resolve().parent.parent.parent / ".secrets")
        # PRETIX_TOKEN = os.getenv("PRETIX_TOKEN")
        self.HEADERS = {"Content-Type": "application/json"}  # {"Authorization": f"Token {PRETIX_TOKEN}"}

        self.id_to_name = None
        self.orders = {}

        self.registered_file = getattr(self.config, "REGISTERED_LOG_FILE", "./registered_log.txt")
        self.REGISTERED_SET = set()

    def load_registered(self) -> None:
        """Load list of registered users from file."""
        try:
            with Path(self.registered_file).open() as f:
                registered = [reg.strip() for reg in f]
                self.REGISTERED_SET = set(registered)
        except Exception:
            _logger.exception("Cannot load registered data, starting from scratch. Error:")

    @tasks.loop(minutes=10.0)
    async def fetch_data(self) -> None:
        """Run refresh_all route from API that reloads ticket data."""
        _logger.info("Refresh tickets from Ticket API %r", self.config.TICKETS_BASE_URL)
        time_start = time()
        await self._update_tickets(f"{self.config.TICKETS_BASE_URL}{self.config.TICKETS_REFRESH_ROUTE}")
        _logger.info("Updated tickets from %r in %r seconds", self.config.TICKETS_BASE_URL, time() - time_start)

    async def _update_tickets(self, url: str) -> bool:
        async with aiohttp.ClientSession() as session, session.get(url, headers=self.HEADERS) as response:
            if response.status == HTTPStatus.OK:
                return True
        _logger.error("Error occurred while updating Ticket API: Status %r", response.status)
        return False

    async def get_ticket_type(self, order: str, full_name: str) -> dict | None:
        """With user input `order` and `full_name`, check for their ticket type."""
        key = f"{order}-{sanitize_string(input_string=full_name)}"
        self.validate_key(key)
        data = None

        async with aiohttp.ClientSession() as session, session.post(
            f"{self.config.TICKETS_BASE_URL}{self.config.TICKETS_VALIDATION_ROUTE}",
            headers=self.HEADERS,
            json={"order_id": order, "name": full_name},
        ) as request:
            if request.status == HTTPStatus.OK:
                data = await request.json()
                if data.get("is_attendee"):
                    self.REGISTERED_SET.add(key)
                    async with aiofiles.open(self.registered_file, mode="a") as f:
                        await f.write(f"{key}\n")
                else:
                    hint = data.get("hint")
                    msg = f"No ticket found - inputs: {order=}, {full_name=}. {hint=}"
                    raise NotFoundError(
                        msg,
                        hint,
                    )
            elif request.status == HTTPStatus.NOT_FOUND:
                _logger.error("Ticket not found - inputs: %r, %r", order, full_name)
            elif request.status == HTTPStatus.UNPROCESSABLE_ENTITY:
                _logger.error("Invalid input - inputs: %r, %r", order, full_name)
            else:
                _logger.error("Error occurred: Status %r", request.status)

        return data

    async def get_roles(self, name: str, order: str) -> list[int]:
        """Get the roles IDs for the user based on their ticket type."""
        roles: list[int] = []
        data = await self.get_ticket_type(full_name=name, order=order)

        if data:
            if data.get("is_attendee"):
                roles.append(self.config.ROLES["Attendee"])  # Attendee
            if data.get("is_speaker"):
                roles.append(self.config.ROLES["Speaker"])  # Speaker
            if data.get("is_sponsor"):
                roles.append(self.config.ROLES["Sponsor"])  # Sponsor
            if data.get("is_organizer"):
                roles.append(self.config.ROLES["Organiser"])  # Organiser
            if data.get("is_volunteer"):
                roles.append(self.config.ROLES["Volunteer"])  # Volunteer
            if data.get("is_remote"):
                roles.append(self.config.ROLES["Remote"])  # Remote
            if data.get("is_onsite"):
                roles.append(self.config.ROLES["On-Site"])  # On-Site
            # TODO(dan): what about these?
            # "is_guest"
            # "online_access"

        return roles

    def validate_key(self, key: str) -> bool:
        """Validate the key for uniqueness."""
        if key in self.REGISTERED_SET:
            msg = f"Ticket already registered - id: {key}"
            raise AlreadyRegisteredError(msg)
        return True
