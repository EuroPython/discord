import asyncio
import datetime
import inspect
from collections.abc import Callable, Coroutine

import arrow
import attrs
from tests.programme_notifications.services import helpers


@attrs.define
class FakeClock:
    """A fake clock that does not actually sleep."""

    now: Callable[[], arrow.Arrow] = arrow.utcnow
    calls: list[arrow.Arrow] = attrs.field(default=attrs.Factory(list), init=False)

    async def sleep_until(self, dt: arrow.Arrow) -> None:
        """Record the datetime, but don't actually sleep."""
        self.calls.append(dt)


@attrs.define
class EternalClock(FakeClock):
    """A clock that sleeps pseudo-eternally, from a test perspective."""

    async def sleep_until(self, dt: arrow.Arrow) -> None:
        """Record the datetime passed and sleep for a very long time."""
        await super().sleep_until(dt)
        await asyncio.sleep(1e10)


async def test_runs_coroutines_at_provided_datetime() -> None:
    """The scheduler schedules coroutines at a specified datetime."""
    # GIVEN an instance of a clock
    clock = FakeClock()
    # AND a scheduler that uses the clock
    scheduler = helpers.AwaitableScheduler(clock=clock)
    # AND several coroutines with await counters to schedule
    n_coroutines = 5
    coroutines = [AwaitCounter.get_coroutine_with_counter() for _ in range(n_coroutines)]
    # AND a datetime to schedule the coroutine at
    at = arrow.Arrow(2023, 7, 19, 12, 15, 4)
    # AND that coroutine being scheduled in the scheduler
    scheduler.schedule_tasks_at(*(c for c, _ in coroutines), at=at)

    # WHEN the scheduler runs until completion
    await scheduler.wait_until_completed()

    # THEN the coroutine was scheduled at the appropriate moment
    assert clock.calls == [arrow.Arrow(2023, 7, 19, 12, 15, 4)] * n_coroutines
    # AND the coroutines were awaited once
    assert all(counter.count == 1 for _, counter in coroutines)


async def test_scheduler_cancels_all_pending_coroutines() -> None:
    """Scheduled tasks can be cancelled, all at once."""
    # GIVEN an instance of a clock
    clock = EternalClock()
    # AND a scheduler that uses the clock
    scheduler = helpers.AwaitableScheduler(clock=clock)
    # AND several schedule tasks at various datetimes
    coroutines = []
    for hour in range(9, 18):
        new_coroutines = [AwaitCounter.get_coroutine_with_counter() for _ in range(5)]
        at = arrow.Arrow(2023, 7, 19, hour, 0, 0)
        scheduler.schedule_tasks_at(*(coro for coro, _ in new_coroutines), at=at)
        coroutines.extend(new_coroutines)

    # WHEN all tasks are cancelled
    scheduler.cancel_all()
    await scheduler.wait_until_completed()

    # THEN no coroutines were awaited
    assert all(counter.count == 0 for _, counter in coroutines)
    # AND all coroutines are closed
    assert all(inspect.getcoroutinestate(coro) == inspect.CORO_CLOSED for coro, _ in coroutines)


async def test_scheduler_does_not_schedule_coroutines_in_the_past() -> None:
    """Can't schedule something in the past!"""
    # GIVEN a fixed value for `now`
    now = arrow.Arrow(2023, 7, 19, 9, 0, 0)
    # AND an instance of a clock that uses that fixed `now`
    clock = FakeClock(now=lambda: now)
    # AND a scheduler that uses the clock
    scheduler = helpers.AwaitableScheduler(clock=clock)
    # AND a coroutine object with await counter
    coroutine, counter = AwaitCounter.get_coroutine_with_counter()

    # WHEN the coroutine is scheduled in the past from the fixed now
    scheduler.schedule_tasks_at(coroutine, at=(now - datetime.timedelta(seconds=1)))
    await scheduler.wait_until_completed()

    # THEN the coroutine is closed
    assert inspect.getcoroutinestate(coroutine) == inspect.CORO_CLOSED
    # BUT it has never been awaited
    assert counter.count == 0


@attrs.define
class AwaitCounter:
    """A simple await counter."""

    count: int = 0

    def increment(self) -> None:
        """Increment the count."""
        self.count += 1

    @classmethod
    def get_coroutine_with_counter(cls) -> tuple[Coroutine[None, None, None], "AwaitCounter"]:
        """Return a coroutine that increments the counter."""
        counter_instance = cls()

        async def coroutine() -> None:
            counter_instance.increment()

        return coroutine(), counter_instance
