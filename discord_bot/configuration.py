"""Configuration module for the Discord bot.

This module provides:
- A Singleton metaclass for ensuring a single instance of the configuration.
- A Config class to load and manage configuration settings from TOML files.
"""

import logging
import os
import sys
from pathlib import Path

import toml

_logger = logging.getLogger(f"bot.{__name__}")


class Singleton(type):  # noqa: D101
    _instances = {}  # noqa: RUF012

    def __call__(cls, *args, **kwargs):  # noqa: ANN002, ANN003, ANN204, D102
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)  # noqa: UP008
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """Config class."""

    _CONFIG_DEFAULT = "config.toml"
    _CONFIG_LOCAL = "config.local.toml"

    def __init__(self) -> None:
        """Init config."""
        # Configuration file
        config = None
        self.BASE_PATH = Path(__file__).resolve().parent
        self.CONFIG_PATH = self._get_config_path(self.BASE_PATH)
        with open(self.CONFIG_PATH) as f:  # noqa: PTH123
            config = toml.loads(f.read())

        if not config:
            _logger.critical("Error: Failed to load the config file at '%s'", self.CONFIG_PATH)
            sys.exit(-1)

        try:
            self.LOG_LEVEL = config.get("logging", {}).get("LOG_LEVEL", "INFO")

            self.CONFERENCE_NAME = config["conference"]["CONFERENCE_NAME"]
            self.CONFERENCE_YEAR = config["conference"]["CONFERENCE_YEAR"]
            self.VOLUNTEER_SHIRT_COLOR = config["conference"].get("VOLUNTEER_SHIRT_COLOR", "volunteer")

            self.GUILD = int(config["server"]["GUILD"])

            # from the config.toml get all keys and values from the [roles] and [cole_colors] section
            self.ROLES = config["roles"]
            self.ROLE_COLORS = config["role_colors"]
            # self.ROLE_IDS = {role: int(role_id) for role, role_id in self.ROLES.items()}

            # Pytanis
            self.PRETALX_EVENT_NAME = config["pytanis"]["PRETALX_EVENT_NAME"]
            # TODO(dan): not required anymore?
            self.LIVESTREAMS_SHEET_ID = os.getenv("LIVESTREAMS_SHEET_ID", "")
            self.LIVESTREAMS_WORKSHEET_NAME = os.getenv("LIVESTREAMS_WORKSHEET_NAME", "")
            # self.LIVESTREAMS_SHEET_ID = config["pytanis"]["LIVESTREAMS_SHEET_ID"]
            # self.LIVESTREAMS_WORKSHEET_NAME = config["pytanis"]["LIVESTREAMS_WORKSHEET_NAME"]

            self.CONFERENCE_AFTERNOON_SESSION_START_TIME = config["programme_notifications"][
                "conference_afternoon_session_start_time"
            ]
            self.VIDEO_URL = config["programme_notifications"]["video_url"]

            if config["server"]["CONFERENCE_SETUP_DONE"]:
                # Registration
                self.REG_CHANNEL_ID = int(config["registration"]["REG_CHANNEL_ID"])
                self.REG_HELP_CHANNEL_ID = int(config["registration"]["REG_HELP_CHANNEL_ID"])
                self.REG_LOG_CHANNEL_ID = int(config["registration"]["REG_LOG_CHANNEL_ID"])

                # Tickets
                self.TICKETS_BASE_URL = config["tickets"]["TICKETS_BASE_URL"]
                self.TICKETS_REFRESH_ROUTE = config["tickets"]["TICKETS_REFRESH_ROUTE"]
                self.TICKETS_VALIDATION_ROUTE = config["tickets"]["TICKETS_VALIDATION_ROUTE"]

                # Job Board
                self.JOB_BOARD_CHANNEL_ID = config["job_board"]["JOB_BOARD_CHANNEL_ID"]
                self.JOB_BOARD_TESTING = config["job_board"]["JOB_BOARD_TESTING"]

        except KeyError:
            _logger.critical(
                "Error encountered while reading '%s'. Ensure that it contains the necessary"
                " configuration fields. If you are using a local override of the main configuration"
                " file, please compare the fields in it against the main `config.toml` file.",
                self.CONFIG_PATH,
            )
            sys.exit(-1)

    def _get_config_path(self, base_path: Path) -> Path:
        """Get the path to the relevant configuration file.

        To make local development easier, the committed configuration
        file used for production can be overridden by a local config
        file: If a local configuration file is present, it is used
        instead of the default configuration file.

        Note that the files are not merged: All keys need to be present
        in the local configuration file. One way of achieving this is to
        make a copy of the committed config file and editing the value
        you want to edit.

        The local config file is added to the `.gitignore`, which means
        is safe to create the file without having to worry about
        accidentally committing development configurations.

        :param base_path: The parent directory of the configuration file
        :return: A path to a configuration file. Note that this path is
          not guaranteed to exist: If the default configuration file is
          deleted and there is no local configuration file, the path
          points to a non-existing file
        """
        local_config = base_path / self._CONFIG_LOCAL
        return local_config if local_config.is_file() else base_path / self._CONFIG_DEFAULT
