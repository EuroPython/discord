from __future__ import annotations

import logging
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path

_logger = logging.getLogger(__name__)


class Config:
    def __init__(self, config_file: Path) -> None:
        # Configuration file
        with config_file.open("rb") as f:
            config = tomllib.load(f)

        # Registration
        self.REG_CHANNEL_NAME: str = config["registration"]["REG_CHANNEL_NAME"]
        self.REG_HELP_CHANNEL_NAME: str = config["registration"]["REG_HELP_CHANNEL_NAME"]
        self.REG_LOG_CHANNEL_NAME: str = config["registration"]["REG_LOG_CHANNEL_NAME"]
        self.REGISTERED_LOG_FILE = Path(config["registration"]["REGISTERED_LOG_FILE"])

        # Pretix
        self.PRETIX_BASE_URL: str = config["pretix"]["PRETIX_BASE_URL"]
        self.PRETIX_CACHE_FILE = Path(config["pretix"]["PRETIX_CACHE_FILE"])

        self.ITEM_TO_ROLES: dict[str, list[str]] = config["item_to_role"]
        self.VARIATION_TO_ROLES: dict[str, list[str]] = config["variation_to_role"]

        # Program Notifications
        self.PROGRAM_API_URL: str = config["program_notifications"]["api_url"]
        self.TIMEZONE_OFFSET: int = config["program_notifications"]["timezone_offset"]
        self.SCHEDULE_CACHE_FILE = Path(config["program_notifications"]["schedule_cache_file"])
        self.LIVESTREAM_URL_FILE = Path(config["program_notifications"]["livestream_url_file"])

        self.MAIN_NOTIFICATION_CANNEL_NAME = config["program_notifications"][
            "main_notification_channel_name"
        ]
        # like {'forum_hall': {'name': 'Forum Hall', 'channel_id': '123456'}}
        self.ROOMS_TO_CHANNEL_NAMES: dict[str, str] = config["program_notifications"][
            "rooms_to_channel_names"
        ]

        # optional testing parameters for program notifications
        if simulated_start_time := config["program_notifications"].get("simulated_start_time"):
            self.SIMULATED_START_TIME = datetime.fromisoformat(simulated_start_time).replace(
                tzinfo=timezone(timedelta(hours=self.TIMEZONE_OFFSET))
            )
        else:
            self.SIMULATED_START_TIME = None

        self.FAST_MODE: bool = config["program_notifications"].get("fast_mode", False)

        # Logging
        self.LOG_LEVEL = config.get("logging", {}).get("LOG_LEVEL", "INFO")

        # Statistics
        self.ROLE_REQUIRED_FOR_STATISTICS = config["server_statistics"]["required_role"]
