"""Task scheduler for the bot."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import TYPE_CHECKING, Protocol

import attrs

if TYPE_CHECKING:
    from collections.abc import Coroutine

    import arrow

    from discord_bot.extensions.programme_notifications.services import clock

_logger = logging.getLogger(f"bot.{__name__}")


class IScheduler(Protocol):
    """Interface for a task scheduler."""

    def __len__(self) -> int:
        """Return the number of scheduled tasks."""
        ...

    def schedule_tasks_at(self, *coroutines: Coroutine, at: arrow.Arrow) -> None:
        """Schedule awaitables at the passed datetime."""

    def cancel_all(self) -> None:
        """Cancel all scheduled tasks."""


@attrs.define
class Scheduler:
    """A task scheduler."""

    _clock: clock.IClock
    _tasks: set[asyncio.Task] = attrs.field(init=False, default=attrs.Factory(set))

    def __len__(self) -> int:
        """Get the number of scheduled tasks."""
        return len(self._tasks)

    def schedule_tasks_at(self, *coroutines: Coroutine[None, None, None], at: arrow.Arrow) -> None:
        """Schedule coroutines to be run at the specified time.

        :param coroutines: One or more coroutines to schedule
        :param at: The datetime to await the coroutines at
        """
        if at < self._clock.now():
            _logger.debug("Attempt to schedule coroutines in the past, ignoring tasks...")
            for coro in coroutines:
                coro.close()
            return

        self._tasks.update(self._schedule_task_at(coro, at=at) for coro in coroutines)

    def cancel_all(self) -> None:
        """Cancel all scheduled tasks."""
        _logger.info("Cancelling all tasks...")
        i = 0
        for task in self._tasks:
            task.cancel()
            i += 1
        _logger.info("Cancelled %r tasks.", i)

    def _schedule_task_at(self, coro: Coroutine[None, None, None], at: arrow.Arrow) -> asyncio.Task:
        """Schedule a task at the specified datetime.

        :param coro: The coroutine to schedule
        :param at: The datetime to await the coroutine at
        :return: The created `asyncio.Task` wrapper
        """
        task = asyncio.create_task(self._delay_task(coro, at=at))
        finalize_task = functools.partial(self._finalize_task, coroutine=coro)
        task.add_done_callback(finalize_task)
        return task

    async def _delay_task(self, coro: Coroutine[None, None, None], at: arrow.Arrow) -> None:
        """Await the coroutine at the specified moment.

        :param coro: The coroutine to await
        :param at: The moment to await the coroutine at
        """
        try:
            await self._clock.sleep_until(at)
        except asyncio.CancelledError:
            # Clean up the coroutine if the schedule task was cancelled
            # before it could be run.
            _logger.debug("Coroutine %r (scheduled at %s) was cancelled during the delay", coro, at)
            raise

        # Once the coroutine is running, prevent it from being cancelled
        # as it's unlikely to be scheduled again when the sessions are
        # rescheduled.
        try:
            await asyncio.shield(coro)
        except asyncio.CancelledError:
            raise
        except Exception:
            _logger.exception("Coroutine %r scheduled at %s failed:", coro, at)
        else:
            _logger.debug("Completed coroutine %r scheduled at %s", coro, at)

    def _finalize_task(self, task: asyncio.Task, coroutine: Coroutine[None, None, None]) -> None:
        """Finalize the scheduled task."""
        self._tasks.remove(task)
        coroutine.close()
