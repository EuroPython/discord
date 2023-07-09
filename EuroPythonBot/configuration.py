import json
import sys
from pathlib import Path

import toml


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self):
        # Configuration file
        config = None
        base_path = Path(__file__).resolve().parent
        config_path = base_path / "config.toml"
        with open(config_path) as f:
            config = toml.loads(f.read())

        if not config:
            print("Error: Failed to load the 'config.toml'")
            sys.exit(-1)

        try:
            # Server
            self.GUILD = int(config["server"]["GUILD"])

            # Registration
            self.REG_CHANNEL_ID = int(config["registration"]["REG_CHANNEL_ID"])
            self.REG_HELP_CHANNEL_ID = int(config["registration"]["REG_HELP_CHANNEL_ID"])
            self.REG_LOG_CHANNEL_ID = int(config["registration"]["REG_LOG_CHANNEL_ID"])

            # Pretix
            self.PRETIX_BASE_URL = config["pretix"]["PRETIX_BASE_URL"]
            self.TICKET_TO_ROLES_JSON = config["pretix"]["TICKET_TO_ROLES_JSON"]

            # Mapping
            with open(
                base_path.joinpath(base_path.joinpath(self.TICKET_TO_ROLES_JSON))
            ) as ticket_to_roles_file:
                ticket_to_roles = json.load(ticket_to_roles_file)

            self.TICKET_TO_ROLE = ticket_to_roles

        except KeyError:
            print(
                f"Error encountered while reading {config_path} "
                "Ensure that it contains 'GUILD', 'REG_CHANNEL', 'REG_HELP_CHANNEL', "
                "'PRETIX_BASE_URL', 'CHECKINLIST_ID', 'TICKET_TO_ROLE'"
                " fields."
            )
            sys.exit(-1)
