import asyncio

from discord_bot.extensions.programme_notifications import services


class AwaitableScheduler(services.Scheduler):
    """Inject a method that waits for tasks to complete.

    This allows for predictable tests, as the event loop can run after
    the action has been taken until the post-conditions can be observed.
    """

    async def wait_until_completed(self) -> None:
        await asyncio.gather(*self._tasks, return_exceptions=True)
