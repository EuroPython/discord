from __future__ import annotations

import logging

from discord import Client, TextChannel
from discord.ext import commands, tasks
from discord.utils import get as discord_get

from europython_discord.program_notifications import session_to_embed
from europython_discord.program_notifications.config import ProgramNotificationsConfig
#from europython_discord.program_notifications.livestream_connector import LivestreamConnector
from europython_discord.program_notifications.program_connector import ProgramConnector

_logger = logging.getLogger(__name__)


class ProgramNotificationsCog(commands.Cog):
    def __init__(self, bot: Client, config: ProgramNotificationsConfig) -> None:
        self.bot = bot
        self.config = config
        self.program_connector = ProgramConnector(
            api_url=self.config.api_url,
            cache_file=self.config.schedule_cache_file,
            simulated_start_time=self.config.simulated_start_time,
            fast_mode=self.config.fast_mode,
        )

        #self.livestream_connector = LivestreamConnector(self.config.livestream_url_file)

        self.notified_sessions = set()
        _logger.info("Cog 'Program Notifications' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self.config.simulated_start_time:
            _logger.info("Running in simulated time mode.")
            _logger.info("Will purge all room channels to avoid pile-up of test notifications.")
            await self.purge_all_room_channels()
            _logger.debug(f"Simulated start time: {self.config.simulated_start_time}")
            _logger.debug(f"Fast mode: {self.config.fast_mode}")
        _logger.info("Starting the session notifier...")
        self.notify_sessions.start()
        _logger.info("Cog 'Program Notifications' is ready")

    async def cog_load(self) -> None:
        """Start schedule updater task."""
        _logger.info(
            "Starting the schedule updater and setting the interval for the session notifier..."
        )
        self.fetch_schedule.start()
        #self.fetch_livestreams.start()
        self.notify_sessions.change_interval(
            seconds=2 if self.config.fast_mode and self.config.simulated_start_time else 60
        )
        _logger.info("Schedule updater started and interval set for the session notifier")

    async def cog_unload(self) -> None:
        """Stop all tasks."""
        _logger.info("Stopping the schedule updater and the session notifier...")
        self.fetch_schedule.stop()
        self.notify_sessions.stop()
        _logger.info("Stopped the schedule updater and the session notifier")

    @tasks.loop(minutes=5)
    async def fetch_schedule(self) -> None:
        _logger.info("Starting the periodic schedule update...")
        await self.program_connector.fetch_schedule()

    #@tasks.loop(minutes=5)
    #async def fetch_livestreams(self) -> None:
    #    _logger.info("Starting the periodic livestream update...")
    #    await self.livestream_connector.fetch_livestreams()
    #    _logger.info("Finished the periodic livestream update.")

    @tasks.loop()
    async def notify_sessions(self) -> None:
        # determine sessions to send notifications for
        sessions_to_notify = []
        for session in await self.program_connector.get_upcoming_sessions():
            if session in self.notified_sessions:
                continue  # already notified
            if len(session.rooms) > 1:
                continue  # announcement or coffee/lunch break
            sessions_to_notify.append(session)

        if not sessions_to_notify:
            return

        main_notification_channel = discord_get(
            self.bot.get_all_channels(), name=self.config.main_notification_channel_name
        )
        await main_notification_channel.send(content="# Sessions starting in 5 minutes:")

        for session in sessions_to_notify:
            room_name = session.rooms[0]
            room_channel = self._get_room_channel(room_name)

            # update room's livestream URL
            #livestream_url = await self.livestream_connector.get_livestream_url(
            #    room_name, session.start.date()
            #)
            #embed = session_to_embed.create_session_embed(session, livestream_url)
            embed = session_to_embed.create_session_embed(session, None)


            await main_notification_channel.send(embed=embed)
            if room_channel is not None:
                #await room_channel.edit(
                #    topic=f"Livestream: [YouTube]({livestream_url})" if livestream_url else ""
                #)
                await room_channel.send(
                    content=f"# Starting in 5 minutes @ {session.rooms[0]}",
                    embed=embed,
                )

            # send session notification message to room and main channel

            self.notified_sessions.add(session)

    async def purge_all_room_channels(self) -> None:
        _logger.info("Purging all room channels...")
        for channel_name in self.config.rooms_to_channel_names.values():
            channel = discord_get(self.bot.get_all_channels(), name=channel_name)
            await channel.purge()
        _logger.info("Purged all room channels.")

    def _get_room_channel(self, room_name: str) -> TextChannel | None:
        channel_name = self.config.rooms_to_channel_names.get(room_name)
        if channel_name is None:
            _logger.warning(f"No notification channel configured for room {room_name!r}")
            return None

        return discord_get(self.bot.get_all_channels(), name=channel_name)
