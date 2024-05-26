import logging

import discord
from discord.ext import commands

from configuration import Config
from error import AlreadyRegisteredError, NotFoundError
from helpers.channel_logging import log_to_channel
from helpers.pretix_connector import PretixConnector

config = Config()
order_ins = PretixConnector()

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
        nickname = self.name.value[:32]  # Limit to the max length
        await interaction.user.edit(nick=nickname)
        await log_to_channel(
            channel=interaction.client.get_channel(config.REG_LOG_CHANNEL_ID),
            interaction=interaction,
            name=self.name.value,
            order=self.order.value,
            roles=roles,
        )
        await interaction.response.send_message(
            f"Thank you {self.name.value}, you are now registered!\n\nAlso, your nickname was"
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

        view = RegistrationView()
        embed = discord.Embed(
            title=_title,
            description=_desc,
            colour=0xFF8331,
        )

        await reg_channel.send(embed=embed, view=view)
