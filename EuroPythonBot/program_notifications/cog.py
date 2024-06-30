import logging

from discord import Client, Embed
from discord.ext import commands, tasks

from configuration import Config
from program_notifications import session_to_embed
from program_notifications.models import Session
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
        self.notified_sessions = set()
        _logger.info("Cog 'Program Notifications' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.purge_all_room_channels()
        self.notify_sessions.start()
        _logger.info("Cog 'Program Notifications' is ready")

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
        _logger.info("Stopped the schedule updater and the session notifier")

    @tasks.loop(minutes=5)
    async def fetch_schedule(self):
        _logger.info("Starting the periodic schedule update...")
        await self.connector.fetch_schedule()

    async def notify_room(self, room: str, embed: Embed, content: str = None):
        """
        Send the given notification to the room channel
        """
        channel_id = config.PROGRAM_CHANNELS[room.lower().replace(" ", "_")]["channel_id"]
        channel = self.bot.get_channel(int(channel_id))
        await channel.send(content=content, embed=embed)

    @tasks.loop(seconds=1)
    async def notify_sessions(self):
        sessions: list[Session] = await self.connector.get_upcoming_sessions()
        sessions_to_notify = [
            session for session in sessions if session not in self.notified_sessions
        ]
        first_message = True

        for session in sessions_to_notify:
            embed = session_to_embed.create_session_embed(session)

            # Notify specific rooms
            for room in session.rooms:
                await self.notify_room(room, embed, content=f"# Starting in 5 minutes @ {room}")

            # Prefix the first message to the main channel with a header
            if first_message:
                await self.notify_room(
                    "Main Channel", embed, content=f"# Sessions starting in 5 minutes:"
                )
                first_message = False
            else:
                await self.notify_room("Main Channel", embed)

            self.notified_sessions.add(session)

    async def purge_all_room_channels(self):
        _logger.info("Purging all room channels...")
        for room in config.PROGRAM_CHANNELS.values():
            channel = self.bot.get_channel(int(room["channel_id"]))
            await channel.purge()
        _logger.info("Purged all room channels channels.")
