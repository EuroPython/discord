"""Commands for organisers."""
import logging

import attrs
import discord
from discord.ext import commands

from extensions.organisers import roles

_logger = logging.getLogger(f"bot.{__name__}")


@attrs.define
class Organisers(commands.Cog):
    """A cog with commands for organisers."""

    _bot: commands.Bot
    _roles: roles.Roles

    @commands.command(name="participants")
    async def participants(self, ctx: commands.Context) -> None:
        """Get statistics about registered participants."""
        embed = discord.Embed(
            title="Participant Statistics 2024",
            colour=16747421,
        )
        counts = self._get_counts(ctx.guild)
        embed.add_field(name="Members (total)", value=counts.everyone, inline=False)
        # embed.add_field(name="Unregistered", value=counts.not_registered, inline=False)
        embed.add_field(name="Attendee", value=counts.attendee, inline=False)
        embed.add_field(name="Sponsors", value=counts.sponsors, inline=False)
        embed.add_field(name="Speakers", value=counts.speakers, inline=False)
        embed.add_field(name="Organisers", value=counts.organisers, inline=False)
        embed.add_field(name="Volunteers", value=counts.volunteers, inline=False)
        embed.add_field(name="Remote Volunteers", value=counts.volunteers_remote, inline=False)
        embed.add_field(name="Onsite", value=counts.onsite, inline=False)
        embed.add_field(name="Remote", value=counts.remote, inline=False)

        await ctx.send(embed=embed)

    def _get_counts(self, guild: discord.Guild) -> "_RoleCount":
        """Get counts of member types.

        :param guild: The guild instance providing the information
        :return: Counts of different roles and pseudo-roles
        """
        return _RoleCount(
            everyone=guild.member_count,
            # not_registered=sum(len(m.roles) == 1 for m in guild.members),
            **{
                role: len(guild.get_role(role_id).members)
                for role, role_id in attrs.asdict(self._roles).items()
            },
        )

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if the message author has the organisers role."""
        return any(role.id == self._roles.organisers for role in ctx.author.roles)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle a command error raised in this class."""
        if isinstance(error, commands.CheckFailure):
            _logger.info(
                "%s (%r) tried to run %r but did not pass the check!",
                ctx.author.display_name,
                ctx.author.id,
                ctx.command.name,
            )
            return
        _logger.error(
            "An error occurred while running command %r:", ctx.command.name, exc_info=error
        )

    def __hash__(self) -> int:
        """Return the hash of this Cog."""
        return hash(id(self))


@attrs.define(frozen=True)
class _RoleCount:
    """Counts of members."""

    everyone: int
    # not_registered: int
    organisers: int
    volunteers: int
    volunteers_remote: int
    speakers: int
    sponsors: int
    attendee: int
    onsite: int
    remote: int
