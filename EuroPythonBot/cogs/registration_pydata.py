import logging

import discord
from discord.ext import commands

from configuration import Config
from error import AlreadyRegisteredError, NotFoundError
from helpers.channel_logging import log_to_channel
from helpers.tito_connector import TitoOrder
from cogs.registration import Registration

config = Config()
order_ins = TitoOrder()

CHANGE_NICKNAME = False

EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"
ZERO_WIDTH_SPACE = "\N{ZERO WIDTH SPACE}"
REGISTERED_LIST = {}

_logger = logging.getLogger(f"bot.{__name__}")


# TODO(dan): make pydata subclass with changes
class RegistrationForm(discord.ui.Modal, title="PyConDE/PyData Berlin 2024 Registration"):
    order = discord.ui.TextInput(
        label="Order",
        required=True,
        min_length=4,
        max_length=6,
        placeholder="5-character combination of capital letters and numbers",
    )

    name = discord.ui.TextInput(
        label="Full Name",
        required=True,
        min_length=3,
        max_length=50,
        style=discord.TextStyle.short,
        placeholder="Your Full Name as printed on your ticket/badge",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Assign the role to the user and send a confirmation message."""

        roles = await order_ins.get_roles(
            name=self.name.value,
            order=self.order.value,
        )
        _logger.info("Assigning %r roles=%r", self.name.value, roles)
        for role in roles:
            role = discord.utils.get(interaction.guild.roles, id=role)
            await interaction.user.add_roles(role)
        if CHANGE_NICKNAME:
            nickname = self.name.value[:32]  # Limit to the max length
            # TODO(dan): change nickname not working, because no admin permission?
            await interaction.user.edit(nick=nickname)
        await log_to_channel(
            channel=interaction.client.get_channel(config.REG_LOG_CHANNEL_ID),
            interaction=interaction,
            name=self.name.value,
            order=self.order.value,
            roles=roles,
        )
        msg = f"Thank you {self.name.value}, you are now registered!"
        
        if CHANGE_NICKNAME:
            msg += (
                "\n\nAlso, your nickname was changed to the name you used to register your ticket. "
                "This is also the name that would be on your conference badge, which means that your nickname can be "
                "your 'virtual conference badge'."
        )
        
        await interaction.response.send_message(msg, ephemeral=True, delete_after=20)

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


class RegistrationPyData(Registration, commands.Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self._title = _title = "Welcome to PyConDE / PyData Berlin 2024 on Discord! 🎉🐍"
        # TODO(dan): update text
        self._desc = (
            "Follow these steps to complete your registration:\n\n"
            f'1️⃣ Click on the green "Register Here {EMOJI_POINT}" button.\n\n'
            '2️⃣ Fill in the "Order" (found by clicking the order URL in your confirmation '
            'email from support@pretix.eu with the Subject: Your order: XXXX) and "Full Name" '
            "(as printed on your ticket/badge).\n\n"
            '3️⃣ Click "Submit". We\'ll verify your ticket and give you your role based on '
            "your ticket type.\n\n"
            "Experiencing trouble? Ask for help in the registration-help channel or from a "
            "volunteer in yellow t-shirt at the conference.\n\n"
            "See you on the server! 🐍💻🎉"
        )
