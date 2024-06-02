from __future__ import annotations

import logging
import os

import discord
from discord import Client, Interaction, Role
from discord.ext import commands, tasks

from configuration import Config
from registration.pretix_connector import PretixConnector
from registration.registration_logger import RegistrationLogger

config = Config()

_logger = logging.getLogger(f"bot.{__name__}")


class RegistrationButton(discord.ui.Button["Registration"]):
    def __init__(self, parent_cog: RegistrationCog):
        super().__init__()
        self.parent_cog = parent_cog
        self.label = "Register here 👈"
        self.style = discord.ButtonStyle.green

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(RegistrationForm(parent_cog=self.parent_cog))


class RegistrationForm(discord.ui.Modal, title="Europython 2023 Registration"):
    def __init__(self, parent_cog: RegistrationCog):
        super().__init__()
        self.parent_cog = parent_cog

    order_field = discord.ui.TextInput(
        label="Order",
        required=True,
        min_length=4,
        max_length=6,
        placeholder="5-character combination of capital letters and numbers",
    )

    name_field = discord.ui.TextInput(
        label="Full Name",
        required=True,
        min_length=3,
        max_length=50,
        style=discord.TextStyle.short,
        placeholder="Your Full Name as printed on your ticket/badge",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Assign nickname and roles to the user and send a confirmation message."""
        name = self.name_field.value
        order = self.order_field.value

        _logger.debug(f"Registration attempt: {order=}, {name=}")
        ticket = self.parent_cog.pretix_connector.get_ticket(order=order, name=name)

        if ticket is None:
            await self.log_error_to_user(
                interaction,
                "We cannot find your ticket. Please double check your input and try again.",
            )
            await self.log_error_to_channel(interaction, f"No ticket found: {order=}, {name=}")
            _logger.info(f"No ticket found: {order=}, {name=}")
            return

        if self.parent_cog.registration_logger.is_registered(ticket):
            await self.log_error_to_user(interaction, "You have already registered.")
            await self.log_error_to_channel(interaction, f"Already registered: {order=}, {name=}")
            _logger.info(f"Already registered: {ticket}")
            return

        role_ids = config.TICKET_TO_ROLE.get(ticket.type)
        if role_ids is None:
            await self.log_error_to_user(interaction, "No ticket found.")
            await self.log_error_to_channel(interaction, f"Ticket without assigned roles: {ticket}")
            _logger.info(f"Ticket without role assignments: {ticket}")
            return

        nickname = name[:32]  # Limit to the max length
        _logger.info("Assigning nickname %r", nickname)
        await interaction.user.edit(nick=nickname)

        roles = [discord.utils.get(interaction.guild.roles, id=role_id) for role_id in role_ids]
        _logger.info("Assigning %r role_ids=%r", name, role_ids)
        await interaction.user.add_roles(*roles)

        await self.log_registration_to_channel(interaction, name=name, order=order, roles=roles)
        await self.log_registration_to_user(interaction, name=name)
        await self.parent_cog.registration_logger.mark_as_registered(ticket)
        _logger.info(f"Registration successful: {order=}, {name=}")

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        _logger.exception("An error occurred!")
        await self.log_error_to_user(interaction, "Something went wrong.")
        await self.log_error_to_channel(interaction, f"{error.__class__.__name__}: {error}")

    @staticmethod
    async def log_registration_to_user(interaction: Interaction, *, name: str) -> None:
        await interaction.response.send_message(
            f"Thank you {name}, you are now registered!\n\n"
            f"Also, your nickname was changed to the name you used to register your ticket. "
            f"This is also the name that would be on your conference badge, which means that "
            f"your nickname can be your 'virtual conference badge'.",
            ephemeral=True,
            delete_after=None,
        )

    @staticmethod
    async def log_registration_to_channel(
        interaction: Interaction, *, name: str, order: str, roles: list[Role]
    ) -> None:
        channel = interaction.client.get_channel(config.REG_LOG_CHANNEL_ID)
        message_lines = [
            f"✅ : **<@{interaction.user.id}> REGISTERED**",
            f"{name=} {order=} roles={[role.name for role in roles]}",
        ]
        await channel.send(content="\n".join(message_lines))

    @staticmethod
    async def log_error_to_user(interaction: Interaction, message: str) -> None:
        await interaction.response.send_message(
            f"{message} If you need help, please contact us in <#{config.REG_HELP_CHANNEL_ID}>.",
            ephemeral=True,
            delete_after=None,
        )

    @staticmethod
    async def log_error_to_channel(interaction: Interaction, message: str) -> None:
        channel = interaction.client.get_channel(config.REG_LOG_CHANNEL_ID)
        await channel.send(content=f"❌ : **<@{interaction.user.id}> ERROR**\n{message}")


class RegistrationCog(commands.Cog):
    def __init__(self, bot: Client):
        self.bot = bot

        self.pretix_connector = PretixConnector(
            url=config.PRETIX_BASE_URL, token=os.environ["PRETIX_TOKEN"]
        )
        self.registration_logger = RegistrationLogger(config.REGISTERED_LOG_FILE)
        _logger.info("Cog 'Registration' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)

        await reg_channel.purge()
        await self.pretix_connector.fetch_pretix_data()

        view = discord.ui.View(timeout=None)  # timeout=None to make it persistent
        view.add_item(RegistrationButton(parent_cog=self))

        welcome_message = create_welcome_message(
            "Follow these steps to complete your registration:\n\n"
            '1️⃣ Click on the green "Register Here 👈" button.\n\n'
            '2️⃣ Fill in the "Order" (found by clicking the order URL in your confirmation '
            'email from support@pretix.eu with the Subject: Your order: XXXXX) and "Full Name" '
            "(as printed on your ticket/badge).\n\n"
            '3️⃣ Click "Submit". We\'ll verify your ticket and assign you your roles based on '
            "your ticket type.\n\n"
            f"Experiencing trouble? Ask for help in the <#{config.REG_HELP_CHANNEL_ID}> channel "
            "or from a volunteer a in yellow t-shirt at the conference.\n\n"
            "See you on the server! 🐍💻🎉"
        )

        await reg_channel.send(embed=welcome_message, view=view)

    async def cog_load(self) -> None:
        """Load the initial schedule."""
        _logger.info("Scheduling periodic pretix update task.")
        self.fetch_pretix_updates.start()

    async def cog_unload(self) -> None:
        """Load the initial schedule."""
        _logger.info("Canceling periodic pretix update task.")
        self.fetch_pretix_updates.cancel()

        _logger.info("Replacing registration form with 'currently offline' message")
        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)
        await reg_channel.purge()
        await reg_channel.send(
            embed=create_welcome_message(
                "The registration bot is currently offline. "
                "We apologize for the inconvenience and are working hard to fix the issue."
            )
        )

    @tasks.loop(minutes=5)
    async def fetch_pretix_updates(self):
        _logger.info("Starting the periodic pretix update...")
        try:
            await self.pretix_connector.fetch_pretix_data()
            _logger.info("Finished the periodic pretix update.")
        except Exception:
            _logger.exception("Periodic pretix update failed")


def create_welcome_message(body: str) -> discord.Embed:
    orange = 0xFF8331
    return discord.Embed(
        title="Welcome to EuroPython 2024 on Discord! 🎉🐍",
        description=body,
        color=orange,
    )
