import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aiohttp

from program_notifications.models import Schedule, Session


class ProgramConnector:
    def __init__(
        self,
        api_url,
        timezone_offset,
        simulated_start_time: datetime | None = None,
        time_multiplier: int = 1,
    ) -> None:
        self._api_url = api_url
        self._timezone_offset = timezone_offset
        self._simulated_start_time = simulated_start_time
        self._time_multiplier = time_multiplier
        self._fetch_lock = asyncio.Lock()
        self.sessions_by_day: dict[datetime, list[Session]] | None = None

    async def fetch_schedule(self) -> None:
        """Fetch schedule data from the Program API and write it to a file in case the API is down."""
        async with self._fetch_lock:
            try:
                with open("cached/schedule.json", "r") as fd:
                    schedule = json.loads(fd.read())
            except (FileNotFoundError, json.JSONDecodeError):
                print("Local schedule file not found or invalid, fetching from API...")
                async with aiohttp.ClientSession() as session:
                    async with session.get(self._api_url) as response:
                        if response.status != 200:
                            raise ValueError(f"Failed to fetch schedule: {response.status}")
                        schedule = await response.json()

                # write schedule to file in case the API goes down
                Path("cached").mkdir(exist_ok=True, parents=True)
                with open("cached/schedule.json", "w") as f:
                    f.write(json.dumps(schedule, indent=2))

            finally:
                schedule = Schedule(**schedule)

            self.sessions_by_day = {}
            for day, day_schedule in schedule.days.items():
                sessions = []
                for event in day_schedule.events:
                    if event.event_type != "session":
                        continue
                    sessions.append(event)
                self.sessions_by_day[day] = sessions

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
        if room == "All Rooms":
            return []
        # upcoming sessions are those that start in 5 minutes or less
        # and the start time is after the current time
        now = await self._get_now()
        sessions = await self.get_sessions_by_date(now.date())
        return [
            session
            for session in sessions
            if room in session.rooms
            and session.start - now <= timedelta(minutes=5)
            and session.start > now
        ]
