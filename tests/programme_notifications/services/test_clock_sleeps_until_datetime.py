import asyncio
from unittest import mock

import arrow
import pytest

from discord_bot.extensions.programme_notifications.services import clock


@pytest.mark.parametrize(
    ("until", "expected_seconds"),
    [
        (arrow.Arrow(2023, 7, 19, 10, 16, 0), 60.0),
        (arrow.Arrow(2030, 7, 19, 10, 15, 0), 220924800.0),
        (arrow.Arrow(2023, 7, 19, 10, 14, 0), 0.0),
        (arrow.Arrow(1999, 1, 2, 3, 18, 0), 0.0),
    ],
)
async def test_clock_sleeps_until_specified_datetime(until: arrow.Arrow, expected_seconds: float) -> None:
    """The clock calculates the seconds and sleeps."""
    # GIVEN a value for `now`
    now = arrow.Arrow(2023, 7, 19, 10, 15, 0)
    # AND a mock sleeper coroutine function
    sleeper = mock.AsyncMock(spec_set=asyncio.sleep)
    # AND a clock that uses that now and sleeper
    clock_instance = clock.Clock(now=lambda: now, sleeper=sleeper)

    # WHEN the clock is instructed to sleep until that datetime
    await clock_instance.sleep_until(until)

    # THEN the clock awaited the sleeper with the required seconds
    sleeper.assert_awaited_once_with(expected_seconds)
