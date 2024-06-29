import logging

import aiohttp
from discord import Client
from discord.ext import commands, tasks

from configuration import Config
from program_notifications import session_to_embed
from program_notifications.program_connector import ProgramConnector

config = Config()
_logger = logging.getLogger(f"bot.{__name__}")


class ProgramNotificationsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot
        self.connector = ProgramConnector(
            api_url=config.PROGRAM_API_URL,
            timezone_offset=config.TIMEZONE_OFFSET,
            cache_file=config.SCHEDULE_CACHE_FILE,
            simulated_start_time=config.SIMULATED_START_TIME,
            time_multiplier=config.TIME_MULTIPLIER,
        )

        # These won't work if we decide to offer program notifications
        # for tutorial days, because there are multiple sessions
        # with the same code on different times. Because they have
        # multiple slots. A better approach would be to use a combination
        # of session code and start time as the hash.
        self.notified_sessions = set()
        self.notified_sessions_all_rooms = set()

        _logger.info("Cog 'Program Notifications' has been initialized")

    async def cog_load(self) -> None:
        """
        Start schedule updater task
        """
        _logger.info("Starting the schedule updater...")
        self.fetch_schedule.start()
        _logger.info("Schedule updater started")

    async def cog_unload(self) -> None:
        """
        Stop all tasks
        """
        _logger.info("Stopping the schedule updater and the session notifier...")
        self.fetch_schedule.stop()
        self.notify_sessions.stop()
        self.notify_to_all_rooms_channels.stop()
        _logger.info("Stopped the schedule updater and the session notifier")

    @tasks.loop(minutes=5)
    async def fetch_schedule(self):
        _logger.info("Starting the periodic schedule update...")
        try:
            await self.connector.fetch_schedule()
            _logger.info("Finished the periodic schedule update.")
        except aiohttp.ClientError as e:
            _logger.error(f"Failed to fetch schedule: {e}. Trying to load from cache...")
            try:
                await self.connector.load_schedule_from_cache()
                _logger.info("Loaded the schedule from cache.")
            except FileNotFoundError:
                _logger.critical("Failed to load schedule from cache.")

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
        upcoming_sessions = await self.connector.get_upcoming_sessions_for_room(room_name)
        if upcoming_sessions:
            embeds = [
                session_to_embed.create_session_embed(session)
                for session in upcoming_sessions
                if session.code not in self.notified_sessions
            ]
            self.notified_sessions.update(session.code for session in upcoming_sessions)
            channel = self.bot.get_channel(int(channel_id))
            for i in range(0, len(embeds), 10):  # Split embeds into chunks of 10
                await channel.send(
                    content=f"# Starting in 5 minutes @ {room_name}",
                    embeds=embeds[i : i + 10],
                )

    @tasks.loop(seconds=1)
    async def notify_to_all_rooms_channels(self):
        """
        Notify all upcoming sessions to "All Rooms" channel
        """
        upcoming_sessions = set()
        for room in config.PROGRAM_CHANNELS.values():
            upcoming_sessions.update(
                await self.connector.get_upcoming_sessions_for_room(room["name"])
            )

        embeds = [
            session_to_embed.create_session_embed(session)
            for session in upcoming_sessions
            if session.code not in self.notified_sessions_all_rooms
        ]
        self.notified_sessions_all_rooms.update(session.code for session in upcoming_sessions)
        if embeds:
            channel_id = config.PROGRAM_CHANNELS["all_rooms"]["channel_id"]
            channel = self.bot.get_channel(int(channel_id))
            for i in range(0, len(embeds), 10):  # Split embeds into chunks of 10
                await channel.send(
                    content="# Sessions starting in 5 minutes:", embeds=embeds[i : i + 10]
                )

    async def purge_all_channels(self):
        _logger.info("Purging all channels...")
        for room in config.PROGRAM_CHANNELS.values():
            channel = self.bot.get_channel(int(room["channel_id"]))
            await channel.purge()
        _logger.info("Purged all channels.")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.purge_all_channels()
        self.notify_sessions.start()
        self.notify_to_all_rooms_channels.start()
        _logger.info("Cog 'Program Notifications' is ready")
