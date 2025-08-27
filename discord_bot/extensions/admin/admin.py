"""Commands for admins.

Run these commands in a channel on the server and tag the bot:
e.g. `@botname count`.
"""

import logging

import attrs
import discord
from discord.ext import commands

from discord_bot.extensions.admin import roles

_logger = logging.getLogger(f"bot.{__name__}")


@attrs.define
class Admin(commands.Cog):
    """A cog with commands for admins."""

    _bot: commands.Bot
    _roles: roles.Roles

    @commands.command(name="count")
    async def participants(self, ctx: commands.Context) -> None:
        """Get statistics about registered participants."""
        embed = discord.Embed(
            title="Participant Statistics",
            colour=16747421,
        )
        counts = self._get_counts(ctx.guild)
        embed.add_field(name="Server member (total)", value=counts.everyone, inline=False)
        embed.add_field(name="Organiser", value=counts.organiser, inline=False)
        embed.add_field(name="Volunteer", value=counts.volunteer, inline=False)
        embed.add_field(name="Attendee", value=counts.attendee, inline=False)
        embed.add_field(name="Speaker", value=counts.speaker, inline=False)
        embed.add_field(name="Session-Chair", value=counts.session_chair, inline=False)
        embed.add_field(name="Sponsor", value=counts.sponsor, inline=False)
        embed.add_field(name="On-Site", value=counts.on_site, inline=False)
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
            **{role: len(guild.get_role(role_id).members) for role, role_id in attrs.asdict(self._roles).items()},
        )

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if the message author has the admin role."""
        try:
            author = ctx.author
            if type(author) is not discord.Member:
                msg = "The 'count' command can only be run in a guild channel."
                _logger.warning(msg)
                await ctx.send(msg)
                return False
            return any(role.name == "Admin" for role in author.roles)
        except Exception as error:
            msg = "An error occurred while checking the command context: %r", error
            _logger.exception(msg)
            return False

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
        _logger.error("An error occurred while running command %r:", ctx.command.name, exc_info=error)

    def __hash__(self) -> int:
        """Return the hash of this Cog."""
        return hash(id(self))


@attrs.define(frozen=True)
class _RoleCount:
    """Counts of members."""

    everyone: int
    organiser: int
    volunteer: int
    attendee: int
    speaker: int
    session_chair: int
    sponsor: int
    on_site: int
    remote: int
