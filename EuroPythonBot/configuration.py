import sys

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
        with open("config.toml") as f:
            config = toml.loads(f.read())

        if not config:
            print("Error: Failed to load the config")
            sys.exit(-1)

        try:
            # Server
            self.GUILD = config["server"]["guild"]

            # Registration
            self.REG_CHANNEL = config["registration"]["channel_id"]
            self.REG_HELP_CHANNEL = config["registration"]["help_channel_id"]
            self.ONLINE_ROLE = config["registration"]["online_role"]
            self.INPERSON_ROLE = config["registration"]["inperson_role"]

        except KeyError:
            print(
                "Error while reading the configuration file. "
                "Make sure it contains all the required field"
            )
            sys.exit(-1)
