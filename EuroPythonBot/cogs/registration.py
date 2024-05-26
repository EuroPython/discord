import logging

import discord
from discord import Client
from discord.ext import commands

from configuration import Config
from error import AlreadyRegisteredError, NotFoundError
from helpers.channel_logging import log_to_channel
from helpers.pretix_connector import PretixConnector

config = Config()
pretix_connector = PretixConnector()

ORANGE = 0xFF8331

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

        roles = await pretix_connector.get_roles(name=name, order=order_id)
        _logger.info("Assigning %r roles=%r", name, roles)
        for role in roles:
            role = discord.utils.get(interaction.guild.roles, id=role)
            await interaction.user.add_roles(role)

        nickname = name[:32]  # Limit to the max length
        await interaction.user.edit(nick=nickname)

        await log_to_channel(
            channel=interaction.client.get_channel(config.REG_LOG_CHANNEL_ID),
            interaction=interaction,
            name=name,
            order=order_id,
            roles=roles,
        )

        await pretix_connector.mark_as_registered(order=order_id, full_name=name)
        await interaction.response.send_message(
            f"Thank you {name}, you are now registered!\n\nAlso, your nickname was"
            f"changed to the name you used to register your ticket. This is also the name that"
            f" would be on your conference badge, which means that your nickname can be your"
            f"'virtual conference badge'.",
            ephemeral=True,
            delete_after=20,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # Make sure we know what the error actually is
        _logger.error("An error occurred!", exc_info=error)

        # log error message in discord channel
        await log_to_channel(
            channel=interaction.client.get_channel(config.REG_LOG_CHANNEL_ID),
            interaction=interaction,
            error=error,
        )
        if isinstance(error, AlreadyRegisteredError):
            _msg = "You have already registered! If you think it is not true"
        elif isinstance(error, NotFoundError):
            _msg = "We cannot find your ticket, double check your input and try again, or"
        else:
            _msg = "Something went wrong,"
        _msg += f" ask for help in <#{config.REG_HELP_CHANNEL_ID}>"
        await interaction.response.send_message(_msg, ephemeral=True, delete_after=180)


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

        embed = discord.Embed(title=title, description=description, color=ORANGE)

        await reg_channel.send(embed=embed, view=view)
