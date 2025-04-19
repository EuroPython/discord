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
        self.conference_name = config.CONFERENCE_NAME
        self.conference_year = config.CONFERENCE_YEAR
        self.roles = config.ROLES
        self.role_colors = config.ROLE_COLORS

        self.category_names = {
            "REGISTRATION": f"{self.conference_year}_REGISTRATION",
            "CONFERENCE": f"{self.conference_year}_CONFERENCE",
            "ROOMS": f"{self.conference_year}_ROOMS",
            "SPONSORS": f"{self.conference_year}_SPONSORS",
        }

        self.role_names_to_ids = {}
        self.channels_to_ids = {}

    async def _setup_categories(self) -> None:
        """YYYY__REGISTRATION, YYYY_CONFERENCE, YYYY_ROOMS, and YYYY_SPONSORS categories."""
        _logger.info("Creating categories for the conference.")
        # Check if the categories already exist
        existing_categories = self.guild.categories
        existing_category_names = {category.name for category in existing_categories}

        # discord permissions after registration: one of the following roles
        conference_permission_overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            discord.Object(id=self.role_names_to_ids["Organiser"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Volunteer"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Attendee"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Speaker"]): discord.PermissionOverwrite(view_channel=True),
            discord.Object(id=self.role_names_to_ids["Sponsor"]): discord.PermissionOverwrite(view_channel=True),
        }
        # category permissions must allow as much as the channel permissions, restrict the channels further if needed
        categories_to_permissions = {
            # 1. REGISTRATION - Open to everyone
            self.category_names["REGISTRATION"]: {
                self.guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                )
            },
            # 2., 3., 4. CONFERENCE, ROOMS, SPONSORS - Visible only to registered roles
            self.category_names["CONFERENCE"]: conference_permission_overwrites,
            self.category_names["ROOMS"]: conference_permission_overwrites,
            self.category_names["SPONSORS"]: conference_permission_overwrites,
        }

        for category, permissions in categories_to_permissions.items():
            if category in existing_category_names:
                msg = f"Category '{category}' already exists."
                _logger.info(msg)
            else:
                msg = f"Creating category '{category}'."
                _logger.info(msg)
                await self.guild.create_category(
                    name=category,
                    # create all channels at position 1. This creates the channels in the order they are created after
                    # the given position (1).
                    position=1,
                    overwrites=permissions,
                )

    async def _setup_conference_channels(self) -> None:
        # 1. Create registration channels: registration and registration-help
        registration_channel = await self.guild.create_text_channel(
            name="registration",
            category=discord.utils.get(self.guild.categories, name=self.category_names["REGISTRATION"]),
            position=1,
            topic=(
                "Register here with your ticket ID to access the conference's discord channels. "
                "Registration worked when you can see the conference's discord channels, e.g. #lobby in the "
                f"{self.category_names['CONFERENCE']} category."
            ),
            overwrites={
                self.guild.me: discord.PermissionOverwrite(
                    send_messages=True, manage_messages=True, read_message_history=True
                ),
                self.guild.default_role: discord.PermissionOverwrite(send_messages=False),
            },
        )
        registration_help_channel = await self.guild.create_text_channel(
            name="registration-help",
            category=discord.utils.get(self.guild.categories, name=self.category_names["REGISTRATION"]),
            position=1,
            topic="Trouble with registering? Ask for help here if something went wrong.",
        )

        _logger.info("Registration channels created successfully.")
        _logger.info("=========================================")
        _logger.info("!!MANUAL WORK REQUIRED!! Update config.toml with the new registration channel IDs:")
        msg = f"\nREG_CHANNEL_ID = {registration_channel.id}\nREG_HELP_CHANNEL_ID = {registration_help_channel.id}"
        _logger.info(msg)
        _logger.info("=========================================")

        # 2. conference channels
        channel_names_and_topics = {
            "lobby": (
                f"""Welcome to the {self.conference_name} conference!
                This is the virtual lobby for all attendees.

                Please respect the code of conduct (see #code-of-conduct channel).

                General guidelines:
                OK to post Open Source Projects
                OK to post about communities
                OK to share talk slides

                No spamming.
                No random message to people you don't know.
                No recruiting messages, sponsors only.
                No product placement.
                """
            ),
            "announcements": "Conference announcements will be posted here.",
            "program-notifications": "Automated program notifications will be posted here.",
            "help": "You need help with something? This is the channel for you.",
            "lost-and-found": "Lost something? Found something? Post it here.",
            "slides": "Slides from the conference can be posted here. Please also add your slides to pretalx.",
            "feedback": "Do you have feedback for the conference? Post it here!",
            "social": "off-topic discussions, plan dinner meetings, and other fun stuff.",
            "pyladies": "Pyladies channel for all Pyladies attendees.",
            "remote-attendees": "Remote attendees can use this channel to connect with each other.",
            "remote-attendees-voice": "",
            # special channels
            "speaker-lounge": (
                "This is the speaker lounge. Only speakers, volunteers, and organisers can see this channel."
            ),
            "voltuneers": ("This is the volunteer lounge. Only volunteers and organisers can see this channel."),
            "sponsor-lounge": (
                "This is the sponsor lounge. Only sponsors, volunteers, and organisers can see this channel."
            ),
            "session-chairs": (
                "This is the session chair lounge. Only session chairs, volunteers, and organisers can see this channel."
            ),
        }

    async def _setup_rooms_channels(self) -> None:
        """Set up conference rooms."""
        _, rooms = self.pretalx_client.rooms(event_slug=self.pretalx_event_name)
        for room in rooms:
            msg = f"Room {room.id}: {room.name.en} - {room.description.en} - {room.capacity}"
            _logger.info(msg)

    async def _setup_categories_and_channels(self) -> None:
        """Set up categories and channels for the conference."""
        _logger.info("Setting up categories and channels for the conference.")
        # Check if the roles already exist
        if not self.role_names_to_ids:
            _logger.info("No roles set. Get roles and IDs from the server.")
            for role in self.guild.roles:
                self.role_names_to_ids[role.name] = role.id

        # make sure the Organiser and Attendee roles are in the role_names_to_ids dict
        for role in ["Organiser", "Volunteer", "Attendee", "Speaker", "Sponsor"]:
            if role not in self.role_names_to_ids:
                msg = f"{role} role not found. Check the server or run the conference_setup script."
                _logger.error(msg)
                msg = f"{role} role not found."
                raise ValueError(msg)

        await self._setup_categories()
        await self._setup_conference_channels()
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
        # await self._create_roles()  # DONE
        await self._setup_categories_and_channels()


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
