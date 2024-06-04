"""Cog that handles programme notifications for EuroPython 2023."""

import logging

import aiohttp
import attrs
from discord.ext import commands, tasks

from . import services

_logger = logging.getLogger(f"bot.{__name__}")


@attrs.define
class ProgrammeNotifications(commands.Cog):
    """Programme Notifier Cog"""

    _bot: commands.Bot
    _aiohttp_session: aiohttp.ClientSession
    _notifier: services.Notifier

    async def cog_load(self) -> None:
        """Load the initial schedule."""
        _logger.info("Scheduling periodic update schedule task.")
        self._update_schedule.start()

    async def cog_unload(self) -> None:
        """Unload the cog in the callback style of discord.py"""
        _logger.debug("Stopping update schedule task")
        self._update_schedule.cancel()
        _logger.debug("Closing aiohttp session")
        await self._aiohttp_session.close()

    @commands.group(name="notifications", case_insensitive=True, invoke_without_command=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def notifications(self, context: commands.Context) -> None:
        """The notifications command group."""
        await context.send_help(context.command)

    @notifications.command(name="refresh")
    @commands.has_guild_permissions(manage_messages=True)
    async def refresh_schedule(self, context: commands.Context) -> None:
        """Refresh the schedule information.

        :param context: The command context
        """
        _logger.info("Forcing a refresh of the schedule notifications!")
        try:
            await self._notifier.schedule_notifications(force=True)
        except Exception:
            _logger.exception("Manually updating the schedule failed:")
            await context.send(":x: Updating the schedule failed...")
        else:
            await context.send(":hugging: Schedule refreshed!")

    @notifications.command(name="stats")
    @commands.has_guild_permissions(manage_messages=True)
    async def stats(self, context: commands.Context) -> None:
        """Get notification statistics.

        :param context: The command context
        """
        await context.send(f"There are currently {len(self._notifier)} scheduled notifications.")

    @tasks.loop(minutes=30.0)
    async def _update_schedule(self) -> None:
        """Update the schedule from Pretalx."""
        _logger.info("Starting the periodic schedule update...")
        await self._notifier.schedule_notifications(force=False)
        _logger.info("Finished the periodic schedule update.")

    @_update_schedule.error
    async def _handle_update_schedule_error(self, exception: Exception) -> None:
        """Handle an update schedule error."""
        _logger.error("Updating the schedule failed!", exc_info=exception)

    def __hash__(self) -> int:
        """Make the Cog hashable.

        :return: The hash of the instance id.
        """
        return hash(id(self))
