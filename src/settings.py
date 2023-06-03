import yaml

with open("../configuration.yaml", "r") as file:
    data = yaml.safe_load(file)

BOT_TOKEN = data.get("bot")[0]["token"]

ONBOARD_CHANNEL_NAME = data.get("discord_channels")[0]["onboard_channel_name"]

ATTENDANT_ROLE_NAME = data.get("discord_role_names")[0]["attendant"]
