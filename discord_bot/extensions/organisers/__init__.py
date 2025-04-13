"""Extension for tools for organisers."""

import toml
from discord.ext import commands

from discord_bot import configuration
from discord_bot.extensions.organisers import organisers, roles


async def setup(bot: commands.Bot) -> None:
    """Set up the organisers extension."""
    config = configuration.Config()
    with config.CONFIG_PATH.open(encoding="utf-8") as config_file:
        raw_roles = toml.load(config_file)["roles"]

    roles_instance = roles.Roles(**{name.lower(): role_id for name, role_id in raw_roles.items()})
    await bot.add_cog(organisers.Organisers(bot=bot, roles=roles_instance))
