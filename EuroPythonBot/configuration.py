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
        config_path = Path("__file__").resolve().parent.joinpath("EuroPythonBot", "config.toml")
        with open(config_path) as f:
            config = toml.loads(f.read())

        if not config:
            print("Error: Failed to load the 'config.toml'")
            sys.exit(-1)

        try:
            # Server
            self.GUILD = config["server"]["guild"]

            # Registration
            self.REG_CHANNEL_ID = config["registration"]["reg_channel_id"]
            self.REG_HELP_CHANNEL_ID = config["registration"]["reg_help_channel_id"]
            self.ONLINE_ROLE = config["registration"]["online_role"]
            self.INPERSON_ROLE = config["registration"]["inperson_role"]

        except KeyError:
            print(
                f"Error encountered while reading {config_path}"
                "Ensure that it contains 'GUILD', 'REG_CHANNEL', 'REG_HELP_CHANNEL', "
                "'ONLINE_ROLE', 'INPERSON_ROLE' fields."
            )
            sys.exit(-1)
