"""Commands for organisers."""

from __future__ import annotations

import logging

from discord import Role
from discord.ext import commands
from discord.utils import get as discord_get
from pydantic import BaseModel

_logger = logging.getLogger(__name__)


class GuildStatisticsConfig(BaseModel):
    required_role: str


class GuildStatisticsCog(commands.Cog):
    """A cog with commands for organisers."""

    def __init__(self, bot: commands.Bot, config: GuildStatisticsConfig) -> None:
        self._bot = bot
        self._required_role_name = config.required_role

    @commands.command(name="participants")
    async def list_participants(self, ctx: commands.Context) -> None:
        """Get statistics about registered participants."""
        # count members and roles, sorted from highest to lowest role
        role_counts: dict[str, int] = {}
        for role in await self.get_ordered_roles(ctx):
            role_counts[role.name] = 0
        for member in ctx.guild.members:
            for role in member.roles:
                role_counts[role.name] += 1

        # send message
        lines = [f"{ctx.author.mention} Participant Statistics:"]
        for role_name, count in role_counts.items():
            lines.append(f"* {count} {role_name.strip('<>@')}")
        await ctx.send(content="\n".join(lines))

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if the requested command shall be executed."""
        # check if user has required role
        required_role = discord_get(ctx.guild.roles, name=self._required_role_name)
        if ctx.author.get_role(required_role.id) is None:
            _logger.info(
                "%s (%r) tried to run %r in %s but does not have the role %s",
                ctx.author.display_name,
                ctx.author.id,
                ctx.command.name,
                ctx.channel.name,
                required_role.name,
            )
            return False

        # check if only users with required role can see the channel
        all_roles = await self.get_ordered_roles(ctx)
        role_index = all_roles.index(required_role)
        next_lower_role = all_roles[role_index + 1]
        if ctx.channel.permissions_for(next_lower_role).view_channel:
            _logger.info(
                "%s (%r) tried to run %r in %s but the channel is visible to next lower role %s",
                ctx.author.display_name,
                ctx.author.id,
                ctx.command.name,
                ctx.channel.name,
                next_lower_role.name,
            )
            return False

        return True

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle a command error raised in this class."""
        _logger.error(
            "An error occurred while running command %r:", ctx.command.name, exc_info=error
        )

    @staticmethod
    async def get_ordered_roles(ctx: commands.Context) -> list[Role]:
        return sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
