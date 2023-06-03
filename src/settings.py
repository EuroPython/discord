import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

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

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")

configuration = yaml.safe_load(configuration)
BOT_ECHO_MODE = configuration.get("bot")["echo_mode"]
ONBOARD_CHANNEL_NAME = configuration.get("discord_channels")[
    "onboard_channel_name"
]
ATTENDANT_ROLE_NAME = configuration.get("discord_role_names")["attendant"]
