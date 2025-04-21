import asyncio
import logging
from pathlib import Path

import aiofiles

from europython_discord.registration.ticket import Ticket

_logger = logging.getLogger(f"bot.{__name__}")


class RegistrationLogger:
    def __init__(self, log_file: Path) -> None:
        """Track tickets which are registered via the Discord bot."""
        self._log_file: Path = log_file
        self._registered_ticket_keys: set[str] = set()

        self._registration_lock = asyncio.Lock()

        # load previously registered tickets
        if log_file.exists():
            ticket_keys = log_file.read_text().splitlines()
            self._registered_ticket_keys.update(ticket_keys)
            _logger.info(f"Loaded {len(ticket_keys)} previously registered tickets")
        else:
            _logger.info("File not found, starting with a fresh registration log (%s)", log_file)

    def is_registered(self, ticket: Ticket) -> bool:
        """Check if a ticket is already registered."""
        return ticket.key in self._registered_ticket_keys

    async def mark_as_registered(self, ticket: Ticket) -> None:
        """Mark a ticket as registered. Raise ValueError if it was registered before."""
        async with self._registration_lock:
            _logger.info(f"Marking ticket as registered: {ticket}")

            if self.is_registered(ticket):
                raise ValueError(f"Ticket {ticket} is already registered")

            self._registered_ticket_keys.add(ticket.key)

            async with aiofiles.open(self._log_file, mode="a") as fp:
                await fp.write(f"{ticket.key}\n")
