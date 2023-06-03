# do not check for line length while prototyping
# flake8: noqa: E501

import sys
from pathlib import Path

import yaml

# Locate and load the configuration
# Inform the user

# TODO - do a real user interface
if len(sys.argv) != 2:
    print("Europython Bot. Pass the configuration file as a second parameter")
    sys.exit(1)

# See ../configuraytion.yaml as example
configuration_yaml_file = sys.argv[1]

try:
    configuration = Path(configuration_yaml_file).read_text(encoding="utf-8")
except FileNotFoundError:
    print(f"Configuration file '{configuration_yaml_file}' not found")
    sys.exit(1)

# from this point, parse the yaml and assign globals

data = yaml.safe_load(configuration)

try:
    secret_text = Path(".env").read_text(encoding="utf-8")
    # quick and dirty env parsing
    secrets = {
        sl.split("=")[0]: sl.split("=")[1]
        for sl in secret_text.splitlines()
        if sl
    }
except FileNotFoundError:
    secrets = {}


DISCORD_BOT_TOKEN = data.get("discord_bot")["token"]
DISCORD_BOT_ECHO_MODE = data.get("discord_bot")["echo_mode"]
DISCORD_SERVER_ID = data.get("discord")["server_id"]

# override secrets from ".env"
if DISCORD_SERVER_ID == "*":
    DISCORD_SERVER_ID = int(secrets.get("DISCORD_SERVER_ID"))
if DISCORD_BOT_TOKEN == "*":
    DISCORD_BOT_TOKEN = secrets.get("DISCORD_BOT_TOKEN")

ONBOARD_CHANNEL_NAME = data.get("discord_channels")["onboard_channel_name"]

ATTENDANT_ROLE_NAME = data.get("discord_role_names")["attendant"]
