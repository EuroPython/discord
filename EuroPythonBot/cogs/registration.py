import logging

import discord
from discord import Client, Interaction
from discord.ext import commands

from configuration import Config
from error import AlreadyRegisteredError, NotFoundError
from helpers.pretix_connector import PretixConnector

config = Config()
pretix_connector = PretixConnector()

_logger = logging.getLogger(f"bot.{__name__}")


class RegistrationButton(discord.ui.Button["Registration"]):
    def __init__(self):
        super().__init__()
        self.label = "Register here 👈"
        self.style = discord.ButtonStyle.green

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(RegistrationForm())


class RegistrationForm(discord.ui.Modal, title="Europython 2023 Registration"):
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
        """Assign the role to the user and send a confirmation message."""

        name = self.name_field.value
        order_id = self.order_field.value

        _logger.debug("Fetching roles from Pretix connector")
        role_ids = await pretix_connector.get_roles(order=order_id, name=name)

        nickname = name[:32]  # Limit to the max length
        _logger.info("Assigning nickname %r", nickname)
        await interaction.user.edit(nick=nickname)

        _logger.info("Assigning %r role_ids=%r", name, role_ids)
        roles = [discord.utils.get(interaction.guild.roles, id=role_id) for role_id in role_ids]
        await interaction.user.add_roles(*roles)

        await self.log_registration_to_channel(
            interaction,
            f"{name=} {order_id=} roles={[role.name for role in roles]}",
        )

        await pretix_connector.mark_as_registered(order=order_id, name=name)
        await interaction.response.send_message(
            f"Thank you {name}, you are now registered!\n\n"
            f"Also, your nickname was changed to the name you used to register your ticket. "
            f"This is also the name that would be on your conference badge, which means that "
            f"your nickname can be your 'virtual conference badge'.",
            ephemeral=True,
            delete_after=None,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        _logger.exception("An error occurred!")

        await self.log_error_to_channel(interaction, f"{error.__class__.__name__}: {error}")

        if isinstance(error, AlreadyRegisteredError):
            _msg = "You have already registered! If you think it is not true"
        elif isinstance(error, NotFoundError):
            _msg = "We cannot find your ticket. Please double check your input and try again, or"
        else:
            _msg = "Something went wrong, please"
        _msg += f" ask for help in <#{config.REG_HELP_CHANNEL_ID}>"
        await interaction.response.send_message(_msg, ephemeral=True, delete_after=None)

    async def log_registration_to_channel(self, interaction: Interaction, message: str) -> None:
        await self._log_to_channel(
            interaction,
            f"✅ : **<@{interaction.user.id}> REGISTERED**\n{message}",
        )

    async def log_error_to_channel(self, interaction: Interaction, message: str) -> None:
        await self._log_to_channel(
            interaction,
            f"❌ : **<@{interaction.user.id}> ERROR**\n{message}",
        )

    @staticmethod
    async def _log_to_channel(interaction: Interaction, message: str) -> None:
        channel = interaction.client.get_channel(config.REG_LOG_CHANNEL_ID)
        await channel.send(content=message)


class Registration(commands.Cog):
    def __init__(self, bot: Client):
        self.bot = bot
        _logger.info("Cog 'Registration' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)

        await reg_channel.purge()
        await pretix_connector.fetch_pretix_data()
        await pretix_connector.load_registered()

        title = "Welcome to EuroPython 2023 on Discord! 🎉🐍"
        description = (
            "Follow these steps to complete your registration:\n\n"
            '1️⃣ Click on the green "Register Here 👈" button.\n\n'
            '2️⃣ Fill in the "Order" (found by clicking the order URL in your confirmation '
            'email from support@pretix.eu with the Subject: Your order: XXXXX) and "Full Name" '
            "(as printed on your ticket/badge).\n\n"
            '3️⃣ Click "Submit". We\'ll verify your ticket and assign you your roles based on '
            "your ticket type.\n\n"
            f"Experiencing trouble? Ask for help in the <#{config.REG_HELP_CHANNEL_ID}> channel "
            "or from a volunteer in yellow t-shirt at the conference.\n\n"
            "See you on the server! 🐍💻🎉"
        )

        view = discord.ui.View(timeout=None)  # timeout=None to make it persistent
        view.add_item(RegistrationButton())

        orange = 0xFF8331
        embed = discord.Embed(title=title, description=description, color=orange)

        await reg_channel.send(embed=embed, view=view)
