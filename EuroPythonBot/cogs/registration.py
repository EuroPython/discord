import traceback

from configuration import Config

import discord
from discord.ext import commands

config = Config()

EMOJI_TICKET = "\N{ADMISSION TICKETS}"
EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"
ZERO_WIDTH_SPACE = "\N{ZERO WIDTH SPACE}"


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
        placeholder="The number you find in your ticket",
        default="XXXX",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Thanks {self.name.value}, you are now registered.!",
            ephemeral=True,
            delete_after=20,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)

        _msg = f"Something went wrong, ask in <#{config.REG_HELP_CHANNEL_ID}>"
        await interaction.response.send_message(_msg, ephemeral=True, delete_after=20)


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

        _title = f"Click the 'Register' button in the message {EMOJI_TICKET}"
        _desc = "A window will appear where you can provide your `Name` and `Order number`."

        view = RegistrationView()
        embed = discord.Embed(
            title=_title,
            description=_desc,
            colour=0xFF8331,
        )

        await reg_channel.send(embed=embed, view=view)
