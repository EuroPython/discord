import traceback
from enum import Enum

import discord
from configuration import Config
from discord.ext import commands

config = Config()

emoji_ticket = "\N{ADMISSION TICKETS}"
emoji_point = "\N{WHITE LEFT POINTING BACKHAND INDEX}"


class RegistrationButton(discord.ui.Button["Registration"]):
    def __init__(self, x: int, y: int, label: str, style: discord.ButtonStyle):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.label = label
        self.style = style

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None

        # Launch the modal form
        await interaction.response.send_modal(RegistrationForm(self.view))


class RegistrationForm(discord.ui.Modal, title="Europython 2023 Registration"):
    def __init__(self, view=None):
        self.view = view
        self.name = discord.ui.TextInput(
            label="Name",
            placeholder="Your name as written in your ticket",
            required=True,
        )

        self.order = discord.ui.TextInput(
            label="Order number",
            placeholder="The number you find in your ticket",
            required=True,
        )

    async def on_submit(self, interaction: discord.Interaction):
        # TODO
        # This class (Roles) and method (registration) should be provided
        # by an external module.
        class Roles(Enum):
            ONLINE = 1
            INPERSON = 2
            INVALID = 3

        def registration(name, order):
            return Roles.ONLINE

        role = registration(self.name.value, self.order.value)

        if role != Roles.INVALID:
            if role == Roles.ONLINE:
                await interaction.user.add_roles(self.view.online_role)
            elif role == Roles.INPERSON:
                await interaction.user.add_roles(self.view.inperson_role)

            await interaction.response.send_message(
                f"Thanks {self.name.value}, you are now registered.!",
                ephemeral=True,
                delete_after=20,
            )
        else:
            await interaction.response.send_message(
                (
                    "There was a problem with the provided information. "
                    f"Try again, or ask for help in <#{config.REG_HELP_CHANNEL}>"
                ),
                ephemeral=True,
                delete_after=20,
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        _msg = f"Something went wrong, ask in <#{config.REG_HELP_CHANNEL}>"
        await interaction.response.send_message(_msg, ephemeral=True, delete_after=20)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


class RegistrationView(discord.ui.View):
    def __init__(self, guild):
        # We don't timeout to have a persistent View
        super().__init__(timeout=None)
        self.value = None
        self.guild = guild

        self.online_role = discord.utils.get(self.guild.roles, name=config.ONLINE_ROLE)
        self.inperson_role = discord.utils.get(self.guild.roles, name=config.INPERSON_ROLE)

        self.add_item(
            RegistrationButton(0, 0, f"Register here {emoji_point}", discord.ButtonStyle.green)
        )


class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = None

    @commands.Cog.listener()
    async def on_ready(self):
        if self.guild is None:
            self.guild = self.bot.get_guild(config.GUILD)

        channel_reg = self.bot.get_channel(config.REG_CHANNEL)
        await channel_reg.purge()

        _title = f"Click the button register in the server {emoji_ticket}"
        _desc = "A window will appear so you can provide your `Name` and `Order number`."

        view = RegistrationView(self.guild)
        embed = discord.Embed(
            title=_title,
            description=_desc,
            colour=0xFF8331,
        )

        await channel_reg.send(embed=embed, view=view)
