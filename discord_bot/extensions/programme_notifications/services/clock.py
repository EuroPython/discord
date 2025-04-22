"""Clock service."""

import asyncio
from collections.abc import Coroutine
from typing import Callable, Protocol

import arrow
import attrs


class IClock(Protocol):
    """A protocol for a clock."""

    now: Callable[[], arrow.Arrow]

    async def sleep_until(self, dt: arrow.Arrow) -> None:
        """Sleep until the passed Arrow datetime.

        :param dt: The `arrow.Arrow` datetime to sleep until
        """


@attrs.define(frozen=True)
class Clock:
    """A clock implementation that allows you to sleep."""

    sleeper: Callable[[float], Coroutine[None, None, None]] = asyncio.sleep
    now: Callable[[], arrow.Arrow] = attrs.field(default=arrow.Arrow.utcnow)

    async def sleep_until(self, dt: arrow.Arrow) -> None:
        """Sleep until the passed Arrow datetime.

        :param dt: The `arrow.Arrow` datetime to sleep until
        """
        seconds_to_sleep = (dt - self.now()).total_seconds()
        await self.sleeper(max(seconds_to_sleep, 0.0))
