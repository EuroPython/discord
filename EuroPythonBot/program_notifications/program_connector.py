import asyncio
import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aiofiles
import aiohttp

from program_notifications.models import Schedule, Session

_logger = logging.getLogger(f"bot.{__name__}")


class ProgramConnector:
    def __init__(
        self,
        api_url: str,
        timezone_offset: int,
        cache_file: str,
        simulated_start_time: datetime | None = None,
        time_multiplier: int = 1,
    ) -> None:
        self._api_url = api_url
        self._timezone_offset = timezone_offset
        self._cache_file = Path(cache_file)
        self._simulated_start_time = simulated_start_time
        self._time_multiplier = time_multiplier
        self._fetch_lock = asyncio.Lock()
        self.sessions_by_day: dict[datetime, list[Session]] | None = None

    async def parse_schedule(self, schedule: dict) -> dict[date, list[Session]]:
        """
        Parse the schedule data and return a dictionary with
        the sessions grouped by date.
        """
        schedule = Schedule(**schedule)

        sessions_by_day = {}
        for day, day_schedule in schedule.days.items():
            sessions = []
            for event in day_schedule.events:
                if event.event_type != "session":
                    continue
                sessions.append(event)
            sessions_by_day[day] = sessions

        return sessions_by_day

    async def fetch_schedule(self) -> None:
        """
        Fetch schedule data from the Program API and
        write it to a file in case the API goes down.
        """
        async with self._fetch_lock:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self._api_url) as response:
                        if response.status == 200:
                            schedule = await response.json()

                            # write schedule to file in case the API goes down
                            Path(self._cache_file).parent.mkdir(exist_ok=True, parents=True)
                            async with aiofiles.open(self._cache_file, "w") as f:
                                await f.write(json.dumps(schedule, indent=2))

                        else:
                            raise aiohttp.ClientResponseError(
                                message=response.reason,
                                history=response.history,
                                request_info=response.request_info,
                            )

            except (aiohttp.ClientResponseError, aiohttp.ClientConnectorError) as e:
                raise aiohttp.ClientError(e)

            self.sessions_by_day = await self.parse_schedule(schedule)

    async def load_schedule_from_cache(self) -> None:
        """
        Load schedule data from a file.
        """
        async with aiofiles.open(self._cache_file, "r") as f:
            schedule = json.loads(await f.read())

        self.sessions_by_day = await self.parse_schedule(schedule)

    async def _get_now(self) -> datetime:
        """Get the current time in the conference timezone."""
        # Calling this for every room makes it miss the 5 minute window,
        # if the time multiplier is too high.
        if self._simulated_start_time:
            elapsed = datetime.now(tz=timezone.utc) - self._simulated_start_time["real_start_time"]
            simulated_now = (
                self._simulated_start_time["simulated_start_time"] + elapsed * self._time_multiplier
            )
            return simulated_now.astimezone(timezone(timedelta(hours=self._timezone_offset)))
        else:
            return datetime.now(tz=timezone(timedelta(hours=self._timezone_offset)))

    async def get_sessions_by_date(self, datetime_now: date) -> list[Session]:
        if self.sessions_by_day is None:
            await self.fetch_schedule()
        return self.sessions_by_day[datetime_now]

    async def get_upcoming_sessions_for_room(self, room: str) -> list[Session]:
        # upcoming sessions are those that start in 5 minutes or less
        # and the start time is after the current time
        now = await self._get_now()
        if self._simulated_start_time:
            print(f"Simulated time: {now}")  # TODO: Do better
        sessions = await self.get_sessions_by_date(now.date())
        return [
            session
            for session in sessions
            if room in session.rooms
            and session.start - now <= timedelta(minutes=5)
            and session.start > now
        ]
