"""Conference setup for discord."""

import logging
import os
from pathlib import Path

import discord
from dotenv import load_dotenv
from pytanis import PretalxClient

from discord_bot import configuration

_logger = logging.getLogger("conference_setup")
_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
_logger.addHandler(console_handler)

load_dotenv(Path(__file__).resolve().parent.parent / ".secrets")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

client = discord.Client(intents=discord.Intents.default())


class ConferenceSetup:
    """Class to set up conference rooms in Discord."""

    def __init__(self, config: configuration.Config) -> None:
        """Initialize the ConferenceSetup class."""
        self.pretalx_client = PretalxClient()

        self.guild = client.get_guild(config.GUILD)

        self.event_name = config.PRETALX_EVENT_NAME
        self.roles = config.ROLES
        self.role_colors = config.ROLE_COLORS

        self.role_names_to_ids = {}
        self.rooms = None

    async def _setup_categories(self) -> None:
        """YYYY_CONFERENCE and YYYY_ROOMS categories."""
        # Also YYYY_TALKS?

    async def _setup_conference_channels(self) -> None:
        pass

    async def _setup_rooms_channels(self) -> None:
        """Set up conference rooms."""
        _, rooms = self.pretalx_client.rooms(self.event_name)
        for room in rooms:
            msg = f"Room {room.id}: {room.name.en} - {room.description.en} - {room.capacity}"
            _logger.info(msg)

    async def _setup_categories_and_channels(self) -> None:
        await self._setup_categories()
        await self._setup_conference_channels()
        await self._setup_rooms_channels()

    async def _create_roles(self) -> None:
        """Create roles for the conference with discord."""
        _logger.info("Creating roles for the conference.")

        # abort if one or more roles already have a value in the config.toml file
        # or if one role name already exists on the server
        existing_discord_role_names = [role.name.upper() for role in self.guild.roles]
        for role_name, role_id in self.roles.items():
            if role_id:
                msg = f"Role {role_name} already exists with ID: {role_id}"
                _logger.info(msg)
                msg = "ABORTING: One or more roles already exist. Check the config.toml file."
                raise ValueError(msg)
            if role_name.upper() in existing_discord_role_names:
                msg = f"Role {role_name} already exists on the server."
                _logger.info(msg)
                msg = "ABORTING: One or more roles already exist. Check the roles on the discord server."
                raise ValueError(msg)

        for role_name in self.roles:
            msg = f"Creating role: {role_name}"
            _logger.info(msg)

            role = await self.guild.create_role(
                name=role_name.title(),
                color=discord.Color.from_str(self.role_colors[role_name]),
                hoist=True,
                mentionable=True,
            )
            msg = f"Created role: {role.name} with ID: {role.id}"
            _logger.info(msg)
            self.role_names_to_ids[role_name] = role.id

        _logger.info("Roles created successfully.")
        _logger.info("=========================================")
        _logger.info("Update config.toml with the new role IDs:")
        msg = "\n".join([f"{role_name}={role_id}" for role_name, role_id in self.role_names_to_ids.items()])
        msg = f"\n{msg}"
        _logger.info(msg)
        _logger.info("=========================================")

    async def start(self) -> None:
        """Set up the conference roles, categories and channels."""
        await self._create_roles()
        # await self._setup_categories_and_channels()


@client.event
async def on_ready() -> None:
    """Event handler for when the bot is ready."""
    msg = f"We have logged in as {client.user}"
    _logger.info(msg)

    _logger.info("Starting conference setup..")
    cs = ConferenceSetup(config=configuration.Config(testing=False))
    await cs.start()
    _logger.info("Conference setup completed.")

    # close the bot after setup
    await client.close()
    _logger.info("Setup completed.")


if __name__ == "__main__":
    """Set up the conference roles, categories, and channels."""
    _logger.info("Starting the Discord bot...")
    client.run(DISCORD_BOT_TOKEN)
