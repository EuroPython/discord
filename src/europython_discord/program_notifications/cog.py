import logging

from discord import Client, Embed
from discord.ext import commands, tasks

from europython_discord.configuration import Config
from europython_discord.program_notifications import session_to_embed
from europython_discord.program_notifications.livestream_connector import LivestreamConnector
from europython_discord.program_notifications.models import Session
from europython_discord.program_notifications.program_connector import ProgramConnector

config = Config()
_logger = logging.getLogger(f"bot.{__name__}")


class ProgramNotificationsCog(commands.Cog):
    def __init__(self, bot: Client) -> None:
        self.bot = bot
        self.program_connector = ProgramConnector(
            api_url=config.PROGRAM_API_URL,
            timezone_offset=config.TIMEZONE_OFFSET,
            cache_file=config.SCHEDULE_CACHE_FILE,
            simulated_start_time=config.SIMULATED_START_TIME,
            fast_mode=config.FAST_MODE,
        )

        self.livestream_connector = LivestreamConnector(config.LIVESTREAM_URL_FILE)

        self.notified_sessions = set()
        _logger.info("Cog 'Program Notifications' has been initialized")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if config.SIMULATED_START_TIME:
            _logger.info("Running in simulated time mode.")
            _logger.info("Will purge all room channels to avoid pile-up of test notifications.")
            await self.purge_all_room_channels()
            _logger.debug(f"Simulated start time: {config.SIMULATED_START_TIME}")
            _logger.debug(f"Fast mode: {config.FAST_MODE}")
        _logger.info("Starting the session notifier...")
        self.notify_sessions.start()
        _logger.info("Cog 'Program Notifications' is ready")

    async def cog_load(self) -> None:
        """Start schedule updater task."""
        _logger.info(
            "Starting the schedule updater and setting the interval for the session notifier..."
        )
        self.fetch_schedule.start()
        self.fetch_livestreams.start()
        self.notify_sessions.change_interval(
            seconds=2 if config.FAST_MODE and config.SIMULATED_START_TIME else 60
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

    @tasks.loop(minutes=5)
    async def fetch_livestreams(self) -> None:
        _logger.info("Starting the periodic livestream update...")
        await self.livestream_connector.fetch_livestreams()
        _logger.info("Finished the periodic livestream update.")

    async def set_room_topic(self, room: str, topic: str) -> None:
        """Set the topic of a room channel."""
        channel_id = config.PROGRAM_CHANNELS[room.lower().replace(" ", "_")]["channel_id"]
        channel = self.bot.get_channel(int(channel_id))
        await channel.edit(topic=topic)

    async def notify_room(self, room: str, embed: Embed, content: str | None = None) -> None:
        """Send the given notification to the room channel."""
        channel_id = config.PROGRAM_CHANNELS[room.lower().replace(" ", "_")]["channel_id"]
        channel = self.bot.get_channel(int(channel_id))
        await channel.send(content=content, embed=embed)

    @tasks.loop()
    async def notify_sessions(self) -> None:
        sessions: list[Session] = await self.program_connector.get_upcoming_sessions()
        sessions_to_notify = [
            session for session in sessions if session not in self.notified_sessions
        ]
        first_message = True

        for session in sessions_to_notify:
            if len(session.rooms) > 1:
                continue  # Don't notify registration sessions

            livestream_url = await self.livestream_connector.get_livestream_url(
                session.rooms[0], session.start.date()
            )

            # Set the channel topic
            await self.set_room_topic(
                session.rooms[0],
                f"Livestream: [YouTube]({livestream_url})" if livestream_url else "",
            )

            embed = session_to_embed.create_session_embed(session, livestream_url)

            # # Notify specific rooms
            # for room in session.rooms:
            await self.notify_room(
                session.rooms[0], embed, content=f"# Starting in 5 minutes @ {session.rooms[0]}"
            )

            # Prefix the first message to the main channel with a header
            if first_message:
                await self.notify_room(
                    "Main Channel", embed, content="# Sessions starting in 5 minutes:"
                )
                first_message = False
            else:
                await self.notify_room("Main Channel", embed)

            self.notified_sessions.add(session)

    async def purge_all_room_channels(self) -> None:
        _logger.info("Purging all room channels...")
        for room in config.PROGRAM_CHANNELS.values():
            channel = self.bot.get_channel(int(room["channel_id"]))
            await channel.purge()
        _logger.info("Purged all room channels channels.")
