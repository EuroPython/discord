import logging
import sys
import tomllib
from pathlib import Path

_logger = logging.getLogger(f"bot.{__name__}")


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
        self.BASE_PATH = Path(__file__).resolve().parent
        self.CONFIG_PATH = self._get_config_path(self.BASE_PATH)
        with self.CONFIG_PATH.open("rb") as f:
            config = tomllib.load(f)

        if not config:
            _logger.critical("Error: Failed to load the config file at '%s'", self.CONFIG_PATH)
            sys.exit(-1)

        try:
            # Registration
            self.REG_CHANNEL_ID = int(config["registration"]["REG_CHANNEL_ID"])
            self.REG_HELP_CHANNEL_ID = int(config["registration"]["REG_HELP_CHANNEL_ID"])
            self.REG_LOG_CHANNEL_ID = int(config["registration"]["REG_LOG_CHANNEL_ID"])
            self.REGISTERED_LOG_FILE = Path(config["registration"]["REGISTERED_LOG_FILE"])

            # Pretix
            self.PRETIX_BASE_URL = config["pretix"]["PRETIX_BASE_URL"]

            role_name_to_id: dict[str, int] = config["roles"]
            self.ITEM_TO_ROLES: dict[str, list[int]] = self._translate_role_names_to_ids(
                config["ticket_to_role"], role_name_to_id
            )
            self.VARIATION_TO_ROLES: dict[str, list[int]] = self._translate_role_names_to_ids(
                config["additional_roles_by_variation"], role_name_to_id
            )

            # Logging
            self.LOG_LEVEL = config.get("logging", {}).get("LOG_LEVEL", "INFO")

        except KeyError:
            _logger.critical(
                "Error encountered while reading '%s'. Ensure that it contains the necessary"
                " configuration fields. If you are using a local override of the main configuration"
                " file, please compare the fields in it against the main `config.toml` file.",
                self.CONFIG_PATH,
            )
            sys.exit(-1)

    @staticmethod
    def _translate_role_names_to_ids(
        mapping: dict[str, list[str]], role_ids_by_name: dict[str, int]
    ) -> dict[str, list[int]]:
        """Parse the ticket mapping from role names to role ids."""
        ticket_to_role_ids = {}

        for ticket_type, roles in mapping.items():
            roles_ids = [role_ids_by_name[role] for role in roles]
            ticket_to_role_ids[ticket_type] = roles_ids

        return ticket_to_role_ids

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
