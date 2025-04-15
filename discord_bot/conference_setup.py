"""Conference setup for discord."""

import logging

from pytanis import PretalxClient

_logger = logging.getLogger(f"bot.{__name__}")


class ConferenceSetup:
    """Class to set up conference rooms in Discord."""

    def __init__(self, event_name: str) -> None:
        """Initialize the ConferenceSetup class."""
        self.client = PretalxClient()
        self.event_name = event_name
        self.rooms = None

    def setup(self) -> None:
        """Set up the conference rooms."""
        _, rooms = self.client.rooms(self.event_name)
        for room in rooms:
            msg = f"Room {room.id}: {room.name.en} - {room.description.en} - {room.capacity}"
            # room.availabilities
            _logger.info(msg)
