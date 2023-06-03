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

BOT_TOKEN = data.get("bot")["token"]
DISCORD_SERVER_ID = data.get("bot")["server_id"]
BOT_ECHO_MODE = data.get("bot")["echo_mode"]

ONBOARD_CHANNEL_NAME = data.get("discord_channels")["onboard_channel_name"]

ATTENDANT_ROLE_NAME = data.get("discord_role_names")["attendant"]
