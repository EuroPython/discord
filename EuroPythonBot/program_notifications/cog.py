from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from discord import Client
from discord.ext import commands, tasks

from configuration import Config
from program_notifications import session_to_embed
from program_notifications.program_connector import ProgramConnector

config = Config()

_logger = logging.getLogger(f"bot.{__name__}")


class ProgramNotificationsCog(commands.Cog):
    def __init__(
        self, bot, simulated_start_time: dict[str, datetime] | None = None, time_multiplier: int = 1
    ):
        self.bot: Client = bot
        self.connector = ProgramConnector(
            api_url=config.PROGRAM_API_URL,
            timezone_offset=config.TIMEZONE_OFFSET,
            simulated_start_time=simulated_start_time or None,
            time_multiplier=time_multiplier,
        )

        # These won't work if we decide to offer program notifications
        # for tutorial days, because there are multiple sessions
        # with the same code on different times. Because they have
        # multiple slots.
        self.notified_sessions = set()
        self.notified_sessions_all_rooms = set()

        _logger.info("Cog 'Program Notifications' has been initialized")

    async def cog_load(self) -> None:
        """
        Start schedule updater task
        """
        _logger.info("Starting schedule updater and session checker")

    async def cog_unload(self) -> None:
        """
        Stop schedule updater task
        """
        _logger.info("Stopping schedule updater and session checker")
        self.fetch_schedule.stop()
        self.notify_sessions.stop()
        self.notify_to_all_rooms_channels.stop()

    @tasks.loop(minutes=5)
    async def fetch_schedule(self):
        _logger.info("Starting the periodic schedule update...")
        try:
            await self.connector.fetch_schedule()
            _logger.info("Finished the periodic schedule update.")
        except Exception:
            _logger.exception("Periodic schedule update failed")

    @tasks.loop(seconds=1)
    async def notify_sessions(self):
        """
        Notify all upcoming sessions to all channels
        """
        for room in config.PROGRAM_CHANNELS.values():
            await self.notify_sessions_to_channel(room["name"], room["channel_id"])

    async def notify_sessions_to_channel(self, room_name: str, channel_id: int):
        """
        Notify the upcoming sessions to the channel
        """
        print(room_name, channel_id)
        upcoming_sessions = await self.connector.get_upcoming_sessions_for_room(room_name)
        for session in upcoming_sessions:
            if session.code not in self.notified_sessions:
                embed = session_to_embed.create_session_embed(session)
                channel = self.bot.get_channel(int(channel_id))
                await channel.send(
                    content=f"# Sessions starting in 5 minutes @ {room_name}", embed=embed
                )
                self.notified_sessions.add(session.code)

    @tasks.loop(seconds=1)
    async def notify_to_all_rooms_channels(self):
        """
        Notify all upcoming sessions to "All Rooms" channel
        """
        upcoming_sessions = set()
        embeds = []
        for room in config.PROGRAM_CHANNELS.values():
            for session in await self.connector.get_upcoming_sessions_for_room(room["name"]):
                upcoming_sessions.add(session)

        for session in upcoming_sessions:
            if session.code not in self.notified_sessions_all_rooms:
                embed = session_to_embed.create_session_embed(session)
                embeds.append(embed)
                self.notified_sessions_all_rooms.add(session.code)
        if embeds:
            channel_id = config.PROGRAM_CHANNELS["all_rooms"]["channel_id"]
            channel = self.bot.get_channel(int(channel_id))
            await channel.send(content="# Sessions starting in 5 minutes:", embeds=embeds)

    async def purge_all_channels(self):
        print("purging all channels")
        for room in config.PROGRAM_CHANNELS.values():
            channel = self.bot.get_channel(int(room["channel_id"]))
            await channel.purge()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.purge_all_channels()
        self.fetch_schedule.start()
        self.notify_sessions.start()
        self.notify_to_all_rooms_channels.start()
        _logger.info("Cog 'Program Notifications' is ready")
