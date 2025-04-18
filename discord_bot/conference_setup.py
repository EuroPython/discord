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

        self.pretalx_event_name = config.PRETALX_EVENT_NAME
        self.conference_year = config.CONFERENCE_YEAR
        self.roles = config.ROLES
        self.role_colors = config.ROLE_COLORS

        self.role_names_to_ids = {}
        self.rooms = None

    async def _setup_categories(self) -> None:
        """YYYY__REGISTRATION, YYYY_CONFERENCE, YYYY_ROOMS, and YYYY_SPONSORS categories."""
        _logger.info("Creating categories for the conference.")
        # Check if the categories already exist
        existing_categories = {category.name for category in self.guild.categories}

        # discord permissions after registration: one of the following roles
        conference_permission_overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            discord.Object(id=self.role_names_to_ids["Organiser"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Volunteer"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Attendee"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Speaker"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Sponsor"]): discord.PermissionOverwrite(view_channel=True),
        }
        categories_to_permissions = {
            # 1. REGISTRATION - Open to everyone
            f"{self.conference_year}_REGISTRATION": discord.PermissionOverwrite(view_channel=True),
            # 2., 3., 4. CONFERENCE, ROOMS, SPONSORS - Visible only to registered roles
            f"{self.conference_year}_CONFERENCE": conference_permission_overwrites,
            f"{self.conference_year}_ROOMS": conference_permission_overwrites,
            f"{self.conference_year}_SPONSORS": conference_permission_overwrites,
        }

        for i, (category, permissions) in enumerate(categories_to_permissions):
            if category in existing_categories:
                msg = f"Category '{category}' already exists."
                _logger.info(msg)
            else:
                msg = f"Creating category '{category}'."
                _logger.info(msg)
                await self.guild.create_category(
                    name=category,
                    position=i + 1,  # create after GENERAL category
                    overwrites=permissions,
                )

    async def _setup_conference_channels(self) -> None:
        pass

    async def _setup_rooms_channels(self) -> None:
        """Set up conference rooms."""
        _, rooms = self.pretalx_client.rooms(event_slug=self.pretalx_event_name)
        for room in rooms:
            msg = f"Room {room.id}: {room.name.en} - {room.description.en} - {room.capacity}"
            _logger.info(msg)

    async def _setup_categories_and_channels(self) -> None:
        categories = self.guild.categories
        _logger.info(categories)
        # await self._setup_categories()
        # await self._setup_conference_channels()
        # await self._setup_rooms_channels()

    def _format_role_name(self, role_name: str) -> str:
        """Format the role name to match the Discord server."""
        return role_name.replace("_", "-").title()

    async def _create_roles(self) -> None:
        """Create roles for the conference with discord."""
        _logger.info("Creating roles for the conference.")

        # abort if one or more roles already have a value in the config.toml file
        # or if one role name already exists on the server
        existing_discord_role_names = []
        for role in self.guild.roles:
            existing_discord_role_names.append(role.name)
            self.role_names_to_ids[role.name] = role.id
        for role_name, role_id in self.roles.items():
            if role_id:
                msg = f"Role '{role_name}' already exists with ID: '{role_id}'."
                _logger.info(msg)
                msg = "ABORTING: One or more roles already exist. Check the config.toml file."
                raise ValueError(msg)
            if role_name.upper() in existing_discord_role_names:
                msg = f"Role '{role_name}' already exists on the server."
                _logger.info(msg)
                msg = "ABORTING: One or more roles already exist. Check the roles on the discord server."
                raise ValueError(msg)

        for role_name in self.roles:
            formatted_role_name = self._format_role_name(role_name)
            msg = f"Creating role: '{formatted_role_name}'"
            _logger.info(msg)

            role = await self.guild.create_role(
                name=formatted_role_name,
                color=discord.Color.from_str(self.role_colors[role_name]),
            )
            msg = f"Created role: '{formatted_role_name}' with ID: '{role.id}'."
            _logger.info(msg)
            self.role_names_to_ids[self._format_role_name(role_name)] = role.id

        _logger.info("Roles created successfully.")
        _logger.info("=========================================")
        _logger.info("!!MANUAL WORK REQUIRED!! Update config.toml with the new role IDs:")
        msg = "\n".join([f"{role_name} = {self.role_names_to_ids[role_name]}" for role_name in self.roles])
        msg = f"\n{msg}"
        _logger.info(msg)
        _logger.info("=========================================")

    async def start(self) -> None:
        """Set up the conference roles, categories and channels."""
        await self._create_roles()
        # await self._setup_categories_and_channels()


@client.event
async def on_ready() -> None:
    """Event handler for when the bot is ready: Do conference setup and log out when it is done."""
    msg = f"We have logged in as '{client.user}'."
    _logger.info(msg)

    _logger.info("Starting conference setup...")
    cs = ConferenceSetup(config=configuration.Config())
    await cs.start()
    _logger.info("Conference setup completed.")

    await client.close()
    msg = f"Logged out '{client.user}'."
    _logger.info(msg)


if __name__ == "__main__":
    """Set up the conference roles, categories, and channels."""
    _logger.info("Starting the Discord client...")
    client.run(DISCORD_BOT_TOKEN)
    _logger.info("Discord client stopped.")
