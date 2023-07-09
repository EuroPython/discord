import traceback

from configuration import Config
from error import AlreadyRegisteredError, NotFoundError
from helpers.logging import display_roles, log_to_channel
from helpers.pretix_connector import PretixOrder

import discord
from discord.ext import commands

config = Config()
order_ins = PretixOrder()

EMOJI_TICKET = "\N{ADMISSION TICKETS}"
EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"
ZERO_WIDTH_SPACE = "\N{ZERO WIDTH SPACE}"
REGISTERED_LIST = {}


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
        print(f"INFO: Assigning {self.name.value} {roles=}")
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
        traceback.print_exception(type(error), error, error.__traceback__)

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
        print("Cog 'Registration' ready")

    @commands.Cog.listener()
    async def on_ready(self):
        if self.guild is None:
            self.guild = self.bot.get_guild(config.GUILD)

        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)

        await reg_channel.purge()
        await order_ins.fetch_data()
        order_ins.load_registered()

        _title = f"Click the 'Register' button in the message {EMOJI_TICKET}"
        _desc = "A window will appear where you can provide your `Name` and `Order number`."

        view = RegistrationView()
        embed = discord.Embed(
            title=_title,
            description=_desc,
            colour=0xFF8331,
        )

        await reg_channel.send(embed=embed, view=view)
