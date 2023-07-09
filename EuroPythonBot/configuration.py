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
    _CONFIG_DEFAULT = "config.toml"
    _CONFIG_LOCAL = "config.local.toml"

    def __init__(self):
        # Configuration file
        config = None
        base_path = Path(__file__).resolve().parent
        config_path = self._get_config_path(base_path)
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
