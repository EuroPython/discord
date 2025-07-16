from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import aiofiles

logger = logging.getLogger(__name__)


class LivestreamConnector:
    def __init__(self, livestreams_file: Path) -> None:
        self._livestreams_file = livestreams_file
        self._fetch_lock = asyncio.Lock()

        # like dict[room, dict[date, url]]
        self.livestreams_by_room: dict[str, dict[date, str]] | None = None

    async def _open_livestreams_file(self) -> dict[str, dict[str, dict[str, str]]]:
        """Open the livestreams file and return its content."""
        async with aiofiles.open(self._livestreams_file) as f:
            return tomllib.loads(await f.read())

    async def _parse_livestreams(
        self, livestreams_raw: dict[str, dict[str, dict[str, str]]]
    ) -> dict[str, dict[date, str]]:
        """Parse livestream data and return a dictionary with the livestreams grouped by room."""
        livestreams_by_room: dict[str, dict[date, str]] = {}

        for room_details in livestreams_raw["rooms"].values():
            room_name = room_details.pop("name")
            livestreams_by_room[room_name] = {
                date.fromisoformat(livestream_date): livestream_url
                for livestream_date, livestream_url in room_details.items()
            }

        return livestreams_by_room

    async def fetch_livestreams(self) -> None:
        """Read the livestreams file and parse it."""
        async with self._fetch_lock:
            livestreams_raw = await self._open_livestreams_file()
            self.livestreams_by_room = await self._parse_livestreams(livestreams_raw)
        logger.info("Fetched %s", self.livestreams_by_room)

    async def get_livestream_url(self, room: str, day: date) -> str | None:
        """
        Get the livestream URL for the given room and date.

        :param room: The room name.
        :param day: The date of the livestream.

        :return: The URL of the livestream.
        """
        if not self.livestreams_by_room:
            await self.fetch_livestreams()

        if room not in self.livestreams_by_room:
            logger.warning(f"Found no livestream URLs for room {room!r}")
            return None
        if day not in self.livestreams_by_room[room]:
            logger.warning(f"Found no livestream URLs for room {room!r} and day {day!r}")
            return None
        return self.livestreams_by_room[room][day]
