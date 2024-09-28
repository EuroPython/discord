from __future__ import annotations

import logging
import os
import textwrap

import discord
from discord import Client, Forbidden, Interaction, Role
from discord.ext import commands, tasks

from configuration import Config
from registration.pretix_connector import PretixConnector
from registration.registration_logger import RegistrationLogger

config = Config()

_logger = logging.getLogger(f"bot.{__name__}")


class RegistrationButton(discord.ui.Button["Registration"]):
    def __init__(self, parent_cog: RegistrationCog):
        super().__init__()
        self.parent_cog = parent_cog
        self.label = "Regístrate aquí 👈"
        self.style = discord.ButtonStyle.green

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(RegistrationForm(parent_cog=self.parent_cog))


class RegistrationForm(discord.ui.Modal, title="PyConES 2024 Registration"):
    def __init__(self, parent_cog: RegistrationCog):
        super().__init__()
        self.parent_cog = parent_cog

    order_field = discord.ui.TextInput(
        label="ID del ticket (como aparece en tu credencial)",
        required=True,
        min_length=5,
        max_length=9,
        placeholder="Algo como '#XXXXX-X' o 'XXXXX'",
    )

    name_field = discord.ui.TextInput(
        label="Nombre (como aparece en tu credencial)",
        required=True,
        min_length=1,
        max_length=50,
        style=discord.TextStyle.short,
        placeholder="Algo como 'Jane Doe'",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Assign nickname and roles to the user and send a confirmation message."""
        name = self.name_field.value
        order = self.order_field.value

        _logger.debug(f"Registration attempt: {order=}, {name=}")
        tickets = self.parent_cog.pretix_connector.get_tickets(order=order, name=name)

        if not tickets:
            await self.log_error_to_user(
                interaction,
                "No podemos encontrar tu ticket. "
                "Por favor, verifica que el ID y el nombre sean correctos.",
            )
            await self.log_error_to_channel(interaction, f"No ticket found: {order=}, {name=}")
            _logger.info(f"No ticket found: {order=}, {name=}")
            return

        if any(self.parent_cog.registration_logger.is_registered(ticket) for ticket in tickets):
            await self.log_error_to_user(interaction, "Ya te has registrado.")
            await self.log_error_to_channel(interaction, f"Already registered: {order=}, {name=}")
            _logger.info(f"Already registered: {tickets}")
            return

        role_ids = set()
        for ticket in tickets:
            if ticket.type in config.ITEM_TO_ROLES:
                role_ids.update(config.ITEM_TO_ROLES[ticket.type])
            if ticket.variation in config.VARIATION_TO_ROLES:
                role_ids.update(config.VARIATION_TO_ROLES[ticket.variation])

        if not role_ids:
            await self.log_error_to_user(interaction, "No se ha encontrado el ticket.")
            await self.log_error_to_channel(interaction, f"Tickets without roles: {tickets}")
            _logger.info(f"Tickets without role assignments: {tickets}")
            return

        nickname = tickets[0].name[:32]  # Limit to the max length
        _logger.info("Assigning nickname %r", nickname)
        await interaction.user.edit(nick=nickname)

        roles = [discord.utils.get(interaction.guild.roles, id=role_id) for role_id in role_ids]
        _logger.info("Assigning %r role_ids=%r", name, role_ids)
        await interaction.user.add_roles(*roles)

        await self.log_registration_to_channel(interaction, name=name, order=order, roles=roles)
        await self.log_registration_to_user(interaction, name=name)
        for ticket in tickets:
            await self.parent_cog.registration_logger.mark_as_registered(ticket)
        _logger.info(f"Registration successful: {order=}, {name=}")

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        user_is_admin = any(role.name == "Admin" for role in interaction.user.roles)
        if isinstance(error, Forbidden) and user_is_admin:
            _logger.exception("An error occurred (user is admin)")
            await self.log_error_to_user(
                interaction, "Los administradores no se pueden registrar usando el bot."
            )
            await self.log_error_to_channel(
                interaction,
                f"Cannot register admins ({error.__class__.__name__}: {error})",
            )

        else:
            _logger.exception("An error occurred!")
            await self.log_error_to_user(interaction, "Algo ha ido mal...")
            await self.log_error_to_channel(interaction, f"{error.__class__.__name__}: {error}")

    @staticmethod
    async def log_registration_to_user(interaction: Interaction, *, name: str) -> None:
        await interaction.response.send_message(
            f"¡Gracias {name}, ya estás registrado!\n\n"
            f"Tu nombre de usuario se ha cambiado para encajar con el que aparece en el ticket. "
            f"Este es también el nombre que aparece en tu credencial, lo que significa que "
            f"tu nombre de usuario es tu 'credencial de acceso virtual'.",
            ephemeral=True,
            delete_after=None,
        )

    @staticmethod
    async def log_registration_to_channel(
        interaction: Interaction, *, name: str, order: str, roles: list[Role]
    ) -> None:
        channel = interaction.client.get_channel(config.REG_LOG_CHANNEL_ID)
        message_lines = [
            f"✅ : **<@{interaction.user.id}> REGISTERED**",
            f"{name=} {order=} roles={[role.name for role in roles]}",
        ]
        await channel.send(content="\n".join(message_lines))

    @staticmethod
    async def log_error_to_user(interaction: Interaction, message: str) -> None:
        await interaction.response.send_message(
            f"{message} If you need help, please contact us in <#{config.REG_HELP_CHANNEL_ID}>.",
            ephemeral=True,
            delete_after=None,
        )

    @staticmethod
    async def log_error_to_channel(interaction: Interaction, message: str) -> None:
        channel = interaction.client.get_channel(config.REG_LOG_CHANNEL_ID)
        await channel.send(content=f"❌ : **<@{interaction.user.id}> ERROR**\n{message}")


class RegistrationCog(commands.Cog):
    def __init__(self, bot: Client):
        self.bot = bot

        self.pretix_connector = PretixConnector(
            url=config.PRETIX_BASE_URL,
            token=os.environ["PRETIX_TOKEN"],
            cache_file=config.PRETIX_CACHE_FILE,
        )
        self.registration_logger = RegistrationLogger(config.REGISTERED_LOG_FILE)
        _logger.info("Cog 'Registration' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)

        await reg_channel.purge()
        await self.pretix_connector.fetch_pretix_data()

        view = discord.ui.View(timeout=None)  # timeout=None to make it persistent
        view.add_item(RegistrationButton(parent_cog=self))

        welcome_message = create_welcome_message(
            textwrap.dedent(
                f"""
                Sigue estos pasos para registrarte en el servidor de la PyConES 2024:

                1️⃣ Haz clic en el botón que dice "Regístrate aquí 👈", justo debajo.

                2️⃣ Rellena el formulario con el ID y el nombre que aparecen en el ticket.
                Puedes encontrarlos:
                * Impresos en tu ticket
                * Impresos en tu credencial
                * En el email "Su pedido: XXXXX" from support@pretix.eu

                3️⃣ Click "Enviar".

                Estos pasos actualizarán tus permisos en el servidor y tu nombre de usuario.

                ¿Tienes algún problema? Por favor, escríbenos en:
                * El canal <#{config.REG_HELP_CHANNEL_ID}>
                * Hablando con algún voluntario que esté en el evento

                ¡Disfruta el servidor de la comunidad PyConES 2024! 🐍💻🎉
                """
            )
        )

        await reg_channel.send(embed=welcome_message, view=view)

    async def cog_load(self) -> None:
        """Load the initial schedule."""
        _logger.info("Scheduling periodic pretix update task.")
        self.fetch_pretix_updates.start()

    async def cog_unload(self) -> None:
        """Load the initial schedule."""
        _logger.info("Canceling periodic pretix update task.")
        self.fetch_pretix_updates.cancel()

        _logger.info("Replacing registration form with 'currently offline' message")
        reg_channel = self.bot.get_channel(config.REG_CHANNEL_ID)
        await reg_channel.purge()
        await reg_channel.send(
            embed=create_welcome_message(
                "El bot de registro está ahora mismo offline. "
                "Pedimos disculpas por el inconveniente. Esperamos que esté disponible pronto."
            )
        )

    @tasks.loop(minutes=5)
    async def fetch_pretix_updates(self):
        _logger.info("Starting the periodic pretix update...")
        try:
            await self.pretix_connector.fetch_pretix_data()
            _logger.info("Finished the periodic pretix update.")
        except Exception:
            _logger.exception("Periodic pretix update failed")


def create_welcome_message(body: str) -> discord.Embed:
    orange = 0xFF8331
    return discord.Embed(
        title="¡Bienvenido a la PyConES 2024 en Discord! 🎉🐍",
        description=body,
        color=orange,
    )
