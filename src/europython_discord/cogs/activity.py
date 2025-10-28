import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

_logger = logging.getLogger(__name__)


class ActivityCog(commands.Cog):
    """Logs server activity to a designated channel.

    By server activity we mean:
    - Member joins/leaves
    - Voice channel joins/leaves
    - Command usage
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.log_channel_id = None  # Can be set via $setlogchannel command or config.toml

    async def log_activity(self, embed: discord.Embed) -> None:
        """Send activity log to the configured channel."""
        if not self.log_channel_id:
            return

        channel = self.bot.get_channel(self.log_channel_id)
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.HTTPException as e:
                _logger.exception("Failed to log activity", exc_info=e)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        """Set the channel for activity logging."""
        self.log_channel_id = channel.id
        await ctx.send(f"Activity log channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Log when a member joins the server."""
        embed = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} ({member.name}#{member.discriminator})",
            color=discord.Color.green(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(
            name="Account Created", value=discord.utils.format_dt(member.created_at, style="R")
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await self.log_activity(embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Log when a member leaves the server."""
        embed = discord.Embed(
            title="Member Left",
            description=f"{member.name}#{member.discriminator}",
            color=discord.Color.red(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(
            name="Joined Server",
            value=discord.utils.format_dt(member.joined_at, style="R")
            if member.joined_at
            else "Unknown",
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await self.log_activity(embed)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        """Log voice channel activity."""
        # Member joined a voice channel
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="Voice Channel Joined",
                description=f"{member.mention} joined {after.channel.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now(tz=timezone.utc),
            )
            embed.set_footer(text=f"ID: {member.id}")
            await self.log_activity(embed)

        # Member left a voice channel
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="Voice Channel Left",
                description=f"{member.mention} left {before.channel.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.now(tz=timezone.utc),
            )
            embed.set_footer(text=f"ID: {member.id}")
            await self.log_activity(embed)

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        """Log when commands are used."""
        embed = discord.Embed(
            title="Command Used",
            description=f"{ctx.author.mention} used `{ctx.command.name}`",
            color=discord.Color.gold(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Channel", value=ctx.channel.mention if ctx.guild else "DM")
        if ctx.args[2:]:  # Skip self and ctx
            embed.add_field(name="Arguments", value=str(ctx.args[2:])[:1024])
        embed.set_footer(text=f"User ID: {ctx.author.id}")
        await self.log_activity(embed)
