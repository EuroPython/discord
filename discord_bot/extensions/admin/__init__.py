"""Extension for tools for admins."""

import toml
from discord.ext import commands

from discord_bot import configuration
from discord_bot.extensions.admin import admin, roles


async def setup(bot: commands.Bot) -> None:
    """Set up the admin extension."""
    config = configuration.Config()
    with config.CONFIG_PATH.open(encoding="utf-8") as config_file:
        raw_roles = toml.load(config_file)["roles"]

    roles_instance = roles.Roles(**{name.replace("-", "_").lower(): role_id for name, role_id in raw_roles.items()})
    await bot.add_cog(admin.Admin(bot=bot, roles=roles_instance))
