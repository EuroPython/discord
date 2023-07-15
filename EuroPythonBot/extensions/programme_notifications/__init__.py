"""Programme Notifications extension for the EuroPython 2023 bot."""
import functools
import logging
import ssl

import aiohttp
import arrow
import certifi
from discord.ext import commands

import configuration as root_configuration

from . import cog, configuration, services
from .domain import repositories

_logger = logging.getLogger(f"bot.{__name__}")


async def setup(bot: commands.Bot) -> None:
    """Set up the Programme Notifications extension."""
    client_session = _create_aiohttp_session()
    session_repository = repositories.SessionRepository()
    config = configuration.NotifierConfiguration.from_environment(root_configuration.Config())

    # Allow for time travel to conference days for test environments
    if config.timewarp:
        _logger.info("Time warping is enabled! Time traveling to the conference days.")
        now = arrow.now(tz=config.timezone)
        # Diff with notifications of first round on first conference day
        diff = arrow.get("2023-07-19T10:39:45+02:00") - now

        def _get_now() -> arrow.Arrow:
            return arrow.now(tz=config.timezone) + diff

    else:
        _logger.info("Using regular time as clock time.")
        _get_now = functools.partial(arrow.now, tz=config.timezone)

    clock = services.Clock(now=_get_now)
    _logger.info("The clock reports that 'now' is '%s'", clock.now())
    scheduler = services.Scheduler(
        clock=clock,
    )
    api_client = services.ApiClient(
        session=client_session,
        config=config,
    )
    session_information = services.SessionInformation(
        api_client=api_client,
        config=config,
        session_repository=session_repository,
    )
    notifier = services.Notifier(
        api_client=api_client,
        config=config,
        scheduler=scheduler,
        session_information=session_information,
    )
    programme_notifications_cog = cog.ProgrammeNotifications(
        bot=bot,
        aiohttp_session=client_session,
        notifier=notifier,
    )
    await bot.add_cog(programme_notifications_cog)


def _create_aiohttp_session() -> aiohttp.ClientSession:
    """Create a ClientSession and return it."""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    return aiohttp.ClientSession(
        connector=connector,
        headers={"User-Agent": "EuroPython Programme Notifier/2023.1"},
        raise_for_status=True,
    )
