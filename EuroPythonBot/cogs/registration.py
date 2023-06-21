import traceback

from helpers.pretix_connector import get_ticket_type

import discord
from discord.ext import commands

EMOJI_TICKET = "\N{ADMISSION TICKETS}"
EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"


class RegistrationButton(discord.ui.Button["Registration"]):
    print("registration button")

    def __init__(self, x: int, y: int, label: str, style: discord.ButtonStyle):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.label = label
        self.style = style

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None

        # Launch the modal form
        await interaction.response.send_modal(RegistrationForm())


class RegistrationForm(discord.ui.Modal, title="EuroPython 2023 Registration"):
    print("RegistrationForm")
    name = discord.ui.TextInput(
        label="Name",
        placeholder="Your name as written in your ticket",
        required=True,
    )

    order = discord.ui.TextInput(
        label="Order number",
        placeholder="The number you find in your ticket",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        print("on_submit")
        print(f"{self.name.value}, {self.order.value}")
        ticket_type = await get_ticket_type(self.order.value, self.name.value)
        # print(ticket_type)
        await interaction.response.send_message(
            f"Thanks, you have {ticket_type}!",
            ephemeral=True,
            delete_after=20,
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        _msg = "Something went wrong, ask in "
        await interaction.response.send_message(_msg, ephemeral=True, delete_after=20)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


class RegistrationView(discord.ui.View):
    def __init__(self, guild):
        super().__init__()
        self.value = None
        self.guild = guild

        self.add_item(
            RegistrationButton(
                0, 0, f"Register here {EMOJI_POINT}", discord.ButtonStyle.green
            )
        )


class Registration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        print("Cog 'Registration' ready")

    # @commands.Cog.listener()
    @commands.hybrid_command(name="reg", description="Get a discord role")
    async def registration_command(self, ctx: commands.Context) -> None:
        print("Registration command triggered")
        _title = f"Click the button register in the server {EMOJI_TICKET}"
        _desc = (
            "A window will appear so you can provide your `Name` and `Order number`."
        )
        view = RegistrationView(ctx.guild)
        embed = discord.Embed(
            title=_title,
            description=_desc,
            colour=0xFF8331,
        )
        await ctx.send(embed=embed, view=view)
