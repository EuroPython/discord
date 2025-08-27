"""Registration cog for EuroPython 2023 Discord bot."""

# ruff: noqa: D101, D107
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from discord_bot.configuration import Config
from discord_bot.error import AlreadyRegisteredError, NotFoundError
from discord_bot.helpers.channel_logging import log_to_channel
from discord_bot.helpers.ticket_connector import TicketOrder

config = Config()
order_ins = TicketOrder()

CHANGE_NICKNAME = True

EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"
ZERO_WIDTH_SPACE = "\N{ZERO WIDTH SPACE}"
REGISTERED_LIST = {}

_logger = logging.getLogger(f"bot.{__name__}")


class RegistrationButton(discord.ui.Button["Registration"]):
    def __init__(
        self,
        registration_form: RegistrationForm,
        x: int = 0,
        y: int = 0,
        label: str = f"Register here {EMOJI_POINT}",
        style: discord.ButtonStyle = discord.ButtonStyle.green,
    ) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label=ZERO_WIDTH_SPACE, row=y)
        self.x = x
        self.y = y
        self.label = label
        self.style = style
        self.registration_form = registration_form

    async def callback(self, interaction: discord.Interaction) -> None:  # noqa: D102
        assert self.view is not None  # noqa: S101

        # Launch the modal form
        await interaction.response.send_modal(self.registration_form())


class RegistrationForm(discord.ui.Modal, title="Europython 2023 Registration"):
    order = discord.ui.TextInput(
        label="Order/Ticket ID (e.g. 'ABCD1')",
        required=True,
        min_length=5,
        max_length=5,
        placeholder="Character combination of 5 capital letters or numbers, e.g. 'ABCD1'.",
    )

    name = discord.ui.TextInput(
        label="Full Name (first and last name)",
        required=True,
        min_length=3,
        # max_length=50,
        style=discord.TextStyle.short,
        placeholder="Your full name as printed on your ticket/badge.",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Assign the role to the user and send a confirmation message."""
        roles = await order_ins.get_roles(
            name=self.name.value,
            order=self.order.value,
        )
        if roles:
            _logger.info("Assigning %r roles=%r", self.name.value, roles)
            for role in roles:
                await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, id=role))
            changed_nickname = True
            if CHANGE_NICKNAME:
                try:
                    # TODO(dan): change nickname not working, because no admin permission?
                    nickname = self.name.value[:32]  # Limit to the max length
                    await interaction.user.edit(nick=nickname)
                except discord.errors.Forbidden as ex:
                    msg = f"Changing nickname for {self.name} did not work: {ex}"
                    _logger.exception(msg)
                    await log_to_channel(
                        channel=interaction.client.get_channel(config.REG_LOG_CHANNEL_ID),
                        interaction=interaction,
                        error=ex,
                    )
                    changed_nickname = False
            await log_to_channel(
                channel=interaction.client.get_channel(config.REG_LOG_CHANNEL_ID),
                interaction=interaction,
                name=self.name.value,
                order=self.order.value,
                roles=roles,
            )
            msg = f"Thank you {self.name.value}, you are now registered!"

            if CHANGE_NICKNAME and changed_nickname:
                msg += (
                    "\n\nAlso, your nickname was changed to the name you used to register your ticket. "
                    "This is also the name that would be on your conference badge, which means that "
                    "your nickname can be your 'virtual conference badge'."
                )
        else:
            error_msg = f"No roles found for name='{self.name.value}' and order='{self.order.value}'."
            _logger.error(error_msg)
            msg = "Something went wrong, please check your input and try again."

            await log_to_channel(
                channel=interaction.client.get_channel(config.REG_LOG_CHANNEL_ID),
                interaction=interaction,
                name=self.name.value,
                order=self.order.value,
                roles=roles,
                error=NotFoundError(error_msg),
            )

        await interaction.response.send_message(msg, ephemeral=True, delete_after=20)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """On error, log the error and send a message to the user."""
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
            _msg = "We cannot find your ticket, double check your input "
            # add hint if available
            if error.args and len(error.args) > 1 and error.args[1]:
                _msg += f"({error.args[1]}) "
            _msg += "and try again, or"
        else:
            _msg = "Something went wrong,"
        _msg += f" ask for help in <#{config.REG_HELP_CHANNEL_ID}>"
        await interaction.response.send_message(_msg, ephemeral=True, delete_after=180)


class RegistrationView(discord.ui.View):
    def __init__(
        self,
        registration_button: RegistrationButton = RegistrationButton,
        registration_form: RegistrationForm = RegistrationForm,
    ) -> None:
        # We don't timeout to have a persistent View
        super().__init__(timeout=None)
        self.value = None
        self.add_item(registration_button(registration_form=registration_form))


class Registration(commands.Cog):
    """Registration cogfor the discord bot."""

    def __init__(self, bot, registration_view: RegistrationView = RegistrationView) -> None:  # noqa: ANN001
        self.bot = bot
        self.guild = None
        self._title = "Welcome to EuroPython 2023 on Discord! 🎉🐍"
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
        self.registration_view = registration_view

        _logger.info("Cog 'Registration' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """On ready start the registration service."""
        if self.guild is None:
            self.guild = self.bot.get_guild(config.GUILD)

        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)

        await reg_channel.purge()
        # start the async fetch_data task with will be triggered automatically using discord tasks
        order_ins.fetch_data.start()
        order_ins.load_registered()

        embed = discord.Embed(
            title=self._title,
            description=self._desc,
            colour=0xFF8331,
        )

        await reg_channel.send(embed=embed, view=self.registration_view())
