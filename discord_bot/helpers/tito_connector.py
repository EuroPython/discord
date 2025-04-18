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


class TitoOrder(metaclass=Singleton):
    def __init__(self):
        self.config = Config()
        load_dotenv(Path(__file__).resolve().parent.parent.parent / ".secrets")
        # PRETIX_TOKEN = os.getenv("PRETIX_TOKEN")
        self.HEADERS = {}  # {"Authorization": f"Token {PRETIX_TOKEN}"}

        self.id_to_name = None
        self.orders = {}

        self.registered_file = getattr(self.config, "REGISTERED_LOG_FILE", "./registered_log.txt")
        self.REGISTERED_SET = set()

    def load_registered(self):
        try:
            f = open(self.registered_file)
            registered = [reg.strip() for reg in f.readlines()]
            self.REGISTERED_SET = set(registered)
            f.close()
        except Exception:
            _logger.exception("Cannot load registered data, starting from scratch. Error:")

    @tasks.loop(minutes=10.0)
    async def fetch_data(self) -> None:
        """Run refresh_all route from API that reloads ticket data from Tito."""
        _logger.info("Refresh tickets from Tito")
        time_start = time()
        await self._update_tito(f"{self.config.TITO_BASE_URL}/tickets/refresh_all")
        _logger.info("Updated tickets from Tito in %r seconds", time() - time_start)

    async def _update_tito(self, url) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.HEADERS) as response:
                if response.status == HTTPStatus.OK:
                    return True
        _logger.error("Error occurred while updating Tito API: Status %r", response.status)
        return False

    async def get_ticket_type(self, order: str, full_name: str) -> dict | None:
        """With user input `order` and `full_name`, check for their ticket type"""
        key = f"{order}-{sanitize_string(input_string=full_name)}"
        self.validate_key(key)
        data = None

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.TITO_BASE_URL}/tickets/validate_name",
                # headers=self.HEADERS,
                json={
                    "ticket_id": order,
                    "name": full_name,
                },
            ) as request:
                if request.status == HTTPStatus.OK:
                    data = await request.json()
                    if data.get("is_attendee"):
                        self.REGISTERED_SET.add(key)
                        async with aiofiles.open(self.registered_file, mode="a") as f:
                            await f.write(f"{key}\n")
                    else:
                        hint = data.get("hint")
                        raise NotFoundError(
                            f"No ticket found - inputs: {order=}, {full_name=}. {hint=}",
                            hint,
                        )
                else:
                    _logger.error("Error occurred: Status %r", request.status)

        return data

    async def get_roles(self, name: str, order: str) -> list[int]:
        roles: list[int] = []
        data = await self.get_ticket_type(full_name=name, order=order)

        # TODO(dan): get role IDs from config
        if data:
            if data.get("is_attendee"):
                roles.append(1164258218655096884)  # Attendee
            if data.get("is_speaker"):
                roles.append(1164258330567516200)  # Speaker
            if data.get("is_sponsor"):
                roles.append(1164258080477945886)  # Sponsor
            if data.get("is_organizer"):
                roles.append(1229442731227484188)  # Organizer
            if data.get("is_volunteer"):
                roles.append(1164258157833490512)  # Volunteer
            if data.get("is_remote"):
                roles.append(1164258270605754428)  # Remote
            if data.get("is_onsite"):
                roles.append(1229516503951347825)  # On-Site

        return roles

    def validate_key(self, key: str) -> bool:
        if key in self.REGISTERED_SET:
            raise AlreadyRegisteredError(f"Ticket already registered - id: {key}")
        return True
