from __future__ import annotations

import logging
import os
import textwrap

import discord
from discord import Client, Forbidden, Interaction, Role
from discord.ext import commands, tasks
from discord.utils import get as discord_get

from europython_discord.registration.config import RegistrationConfig
from europython_discord.registration.pretix_connector import PretixConnector
from europython_discord.registration.registration_logger import RegistrationLogger

_logger = logging.getLogger(__name__)

# Discord's colon-syntax `:point_left:` does not work in button labels, so we use `\N{...}` here
REGISTRATION_BUTTON_LABEL = "Register here \N{WHITE LEFT POINTING BACKHAND INDEX}"
WELCOME_MESSAGE_TITLE = "## Welcome to PyLadiesCon 2025 on Discord! :tada::snake:"


class RegistrationForm(discord.ui.Modal, title="PyLadiesCon 2025 Registration"):
    def __init__(
        self,
        config: RegistrationConfig,
        pretix_connector: PretixConnector,
        registration_logger: RegistrationLogger,
    ) -> None:
        super().__init__()
        self.config = config
        self.pretix_connector = pretix_connector
        self.registration_logger = registration_logger

    order_field = discord.ui.TextInput(
        label="Order ID (As in your ticket)",
        required=True,
        min_length=5,
        max_length=9,
        placeholder="Like '#XXXXX-X' or 'XXXXX'",
    )

    name_field = discord.ui.TextInput(
        label="Name (As in your ticket)",
        required=True,
        min_length=1,
        max_length=50,
        style=discord.TextStyle.short,
        placeholder="Like 'Jane Doe'",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Assign nickname and roles to the user and send a confirmation message."""
        name = self.name_field.value
        order = self.order_field.value

        _logger.info(f"Registration attempt: {order=}, {name=}")
        tickets = self.pretix_connector.get_tickets(order=order, name=name)

        if not tickets:
            await self.log_error_to_user(
                interaction,
                (
                    "We cannot find your ticket. Please double check your input and try again.\n\n"
                    "If you just bought your ticket, please try again in a few minutes."
                ),
            )
            await self.log_error_to_channel(interaction, f"No ticket found: {order=}, {name=}")
            _logger.info(f"No ticket found: {order=}, {name=}")
            return

        if any(self.registration_logger.is_registered(ticket) for ticket in tickets):
            await self.log_error_to_user(interaction, "You have already registered.")
            await self.log_error_to_channel(interaction, f"Already registered: {order=}, {name=}")
            _logger.info(f"Already registered: {tickets}")
            return

        role_names = set()
        for ticket in tickets:
            if ticket.type in self.config.item_to_roles:
                role_names.update(self.config.item_to_roles[ticket.type])
            if ticket.variation in self.config.variation_to_roles:
                role_names.update(self.config.variation_to_roles[ticket.variation])

        if not role_names:
            await self.log_error_to_user(
                interaction,
                "No such conference ticket found. Did you use another ticket (e.g. Social Event)?",
            )
            await self.log_error_to_channel(interaction, f"Tickets without roles: {tickets}")
            _logger.info(f"Tickets without role assignments: {tickets}")
            return

        nickname = tickets[0].name[:32]  # Limit to the max length
        _logger.info("Assigning nickname %r", nickname)
        await interaction.user.edit(nick=nickname)

        roles = [discord_get(interaction.guild.roles, name=role_name) for role_name in role_names]
        if any(role is None for role in roles):
            await self.log_error_to_user(interaction, "Internal error, please contact us.")
            await self.log_error_to_channel(interaction, f"Found invalid role in {role_names}")
            _logger.error("At least one of the role names %s is invalid", role_names)
            return

        _logger.info("Assigning %r role_names=%r", name, role_names)
        await interaction.user.add_roles(*roles)

        await self.log_registration_to_channel(interaction, name=name, order=order, roles=roles)
        await self.log_registration_to_user(interaction, name=nickname)
        await self.registration_logger.mark_as_registered(tickets[0])
        _logger.info(f"Registration successful: {order=}, {name=}")

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        user_is_admin = any(role.name == "Admin" for role in interaction.user.roles)
        if isinstance(error, Forbidden) and user_is_admin:
            _logger.exception("An error occurred (user is admin)")
            await self.log_error_to_user(interaction, "Admins cannot be registered via the bot.")
            await self.log_error_to_channel(
                interaction,
                f"Cannot register admins ({error.__class__.__name__}: {error})",
            )

        else:
            _logger.exception("An error occurred!")
            await self.log_error_to_user(interaction, "Something went wrong.")
            await self.log_error_to_channel(interaction, f"{error.__class__.__name__}: {error}")

    @staticmethod
    async def log_registration_to_user(interaction: Interaction, *, name: str) -> None:
        await interaction.response.send_message(
            f"Thank you {name}, you are now registered!\n\n"
            f"Also, your nickname was changed to the name you used to register your ticket. ",
            ephemeral=True,
            delete_after=None,
        )

    async def log_registration_to_channel(
        self, interaction: Interaction, *, name: str, order: str, roles: list[Role]
    ) -> None:
        channel = discord_get(
            interaction.client.get_all_channels(), name=self.config.registration_log_channel_name
        )
        message_lines = [
            f":white_check_mark: **{interaction.user.mention} REGISTERED**",
            f"{name=} {order=} roles={[role.name for role in roles]}",
        ]
        await channel.send(content="\n".join(message_lines))

    async def log_error_to_user(self, interaction: Interaction, message: str) -> None:
        reg_help_channel = discord_get(
            interaction.guild.channels, name=self.config.registration_help_channel_name
        )
        await interaction.response.send_message(
            f"{message} If you need help, please contact us in {reg_help_channel.mention}.",
            ephemeral=True,
            delete_after=None,
        )

    async def log_error_to_channel(self, interaction: Interaction, message: str) -> None:
        channel = discord_get(
            interaction.client.get_all_channels(), name=self.config.registration_log_channel_name
        )
        await channel.send(content=f":x: **{interaction.user.mention} ERROR**\n{message}")


class RegistrationCog(commands.Cog):
    def __init__(self, bot: Client, config: RegistrationConfig) -> None:
        self.bot = bot
        self.config = config

        self.pretix_connector = PretixConnector(
            url=self.config.pretix_base_url,
            token=os.environ["PRETIX_TOKEN"],
            cache_file=self.config.pretix_cache_file,
        )
        self.registration_logger = RegistrationLogger(self.config.registered_cache_file)
        _logger.info("Cog 'Registration' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.pretix_connector.fetch_pretix_data()

        button = discord.ui.Button(style=discord.ButtonStyle.green, label=REGISTRATION_BUTTON_LABEL)
        button.callback = lambda interaction: interaction.response.send_modal(
            RegistrationForm(
                config=self.config,
                pretix_connector=self.pretix_connector,
                registration_logger=self.registration_logger,
            )
        )
        view = discord.ui.View(timeout=None)  # timeout=None to make it persistent
        view.add_item(button)

        reg_help_channel = discord_get(
            self.bot.get_all_channels(), name=self.config.registration_help_channel_name
        )
        welcome_message = textwrap.dedent(
            f"""
            {WELCOME_MESSAGE_TITLE}\n
            Follow these steps to complete your registration:

            :one: Click on the green "{REGISTRATION_BUTTON_LABEL}" button below.

            :two: Fill in your Order ID and the name on your ticket. You can find them
            * Printed on your ticket
            * In the email "[PyLadiesCon 2025] Your order: XXXXX" from support@pretix.eu

            :three: Click "Submit".

            These steps will assign the correct server permissions and set your server nickname.

            Experiencing trouble? Please contact us
            * In the {reg_help_channel.mention} channel
            * By speaking to a volunteer in a yellow t-shirt

            Enjoy our PyLadiesCon 2025 Community Server! :snake::computer::tada:
            """
        )

        channel = discord_get(
            self.bot.get_all_channels(), name=self.config.registration_form_channel_name
        )
        await channel.purge()
        await channel.send(welcome_message, view=view)

    async def cog_load(self) -> None:
        """Load the initial schedule."""
        _logger.info("Scheduling periodic pretix update task.")
        self.fetch_pretix_updates.start()

    async def cog_unload(self) -> None:
        """Load the initial schedule."""
        _logger.info("Canceling periodic pretix update task.")
        self.fetch_pretix_updates.cancel()

        _logger.info("Replacing registration form with 'currently offline' message")
        reg_channel = discord_get(
            self.bot.get_all_channels(), name=self.config.registration_form_channel_name
        )
        await reg_channel.purge()
        await reg_channel.send(
            f"{WELCOME_MESSAGE_TITLE}\n"
            "The registration bot is currently offline. "
            "We apologize for the inconvenience and are working hard to fix the issue."
        )

    @tasks.loop(minutes=5)
    async def fetch_pretix_updates(self) -> None:
        _logger.info("Starting the periodic pretix update...")
        try:
            await self.pretix_connector.fetch_pretix_data()
            _logger.info("Finished the periodic pretix update.")
        except Exception:
            _logger.exception("Periodic pretix update failed")
