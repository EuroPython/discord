import logging

from configuration import Config
from error import AlreadyRegisteredError, NotFoundError
from helpers.channel_logging import display_roles, log_to_channel
from helpers.pretix_connector import PretixOrder

import discord
from discord.ext import commands

config = Config()
order_ins = PretixOrder()

EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"
ZERO_WIDTH_SPACE = "\N{ZERO WIDTH SPACE}"
REGISTERED_LIST = {}

_logger = logging.getLogger(f"bot.{__name__}")


class RegistrationButton(discord.ui.Button["Registration"]):
    def __init__(self, x: int, y: int, label: str, style: discord.ButtonStyle):
        super().__init__(style=discord.ButtonStyle.secondary, label=ZERO_WIDTH_SPACE, row=y)
        self.x = x
        self.y = y
        self.label = label
        self.style = style

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None

        # Launch the modal form
        await interaction.response.send_modal(RegistrationForm())


class RegistrationForm(discord.ui.Modal, title="Europython 2023 Registration"):
    name = discord.ui.TextInput(
        label="Name",
        required=True,
        min_length=3,
        max_length=50,
        style=discord.TextStyle.short,
        placeholder="Your name as written in your ticket",
        default="My Name",
    )

    order = discord.ui.TextInput(
        label="Order number",
        required=True,
        min_length=4,
        max_length=6,
        placeholder="The number you find in your ticket",
        default="XXXXX",
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
        await log_to_channel(interaction.client.get_channel(config.REG_LOG_CHANNEL_ID), interaction)
        await interaction.response.send_message(
            f"Thank you {self.name.value}, you are now registered as {display_roles(interaction.user)}",  # noqa: E501
            ephemeral=True,
            delete_after=20,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # Make sure we know what the error actually is
        _logger.error("An error occurred!", exc_info=error)

        # log error message in discord channel
        await log_to_channel(
            interaction.client.get_channel(config.REG_LOG_CHANNEL_ID), interaction, error
        )
        if isinstance(error, AlreadyRegisteredError):
            _msg = "You have already registered! If you think it is not true"
        elif isinstance(error, NotFoundError):
            _msg = "We cannot find your ticket, double check your input and try again, or"
        else:
            _msg = "Something went wrong,"
        _msg += f" ask for help in <#{config.REG_HELP_CHANNEL_ID}>"
        await interaction.response.send_message(_msg, ephemeral=True, delete_after=180)


class RegistrationView(discord.ui.View):
    def __init__(self):
        # We don't timeout to have a persistent View
        super().__init__(timeout=None)
        self.value = None
        self.add_item(
            RegistrationButton(0, 0, f"Register here {EMOJI_POINT}", discord.ButtonStyle.green)
        )


class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = None
        _logger.info("Cog 'Registration' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        if self.guild is None:
            self.guild = self.bot.get_guild(config.GUILD)

        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)

        await reg_channel.purge()
        await order_ins.fetch_data()
        order_ins.load_registered()

        _title = "Welcome to EuroPython 2023 on Discord! 🎉🐍"
        _desc = (
            "We're thrilled that you're joining us. "
            "Before you dive into the various conversations happening around here, we need to"
            " confirm your registration details.\n\n"
            f'1️⃣ To start, locate the green "Register here {EMOJI_POINT}" button and give '
            "it a click. A new window will appear for you.\n\n"
            '2️⃣ In this new window, you\'ll find two fields - "Order" and "Full Name." '
            "The Order is a combination of capital letters and numbers that you can locate "
            "either on your ticket or badge. Your Full Name should match the one printed on "
            "your ticket or badge.\n\n"
            '3️⃣ After filling in these details, please click "Submit". We\'ll validate your '
            "ticket and assign you the appropriate role on the Discord server based on your "
            "ticket type. Once this is done, you'll gain access to a collection of channels "
            "that correspond to your ticket type. This is where the magic happens and where "
            "you'll be able to connect, learn, and share with fellow Python enthusiasts.\n"
            "If you encounter any issues during the registration process, or if you're not"
            " sure about something, don't worry! There's always help available. Reach out to "
            "us in the registration-help channel or seek assistance from any of the volunteers "
            "in yellow t-shirts during the conference. They're here to make your experience "
            "smooth and enjoyable!\n"
            "We're looking forward to seeing you on the server and making the most of "
            "EuroPython 2023 together 🐍💻🎉"
        )

        view = RegistrationView()
        embed = discord.Embed(
            title=_title,
            description=_desc,
            colour=0xFF8331,
        )

        await reg_channel.send(embed=embed, view=view)
