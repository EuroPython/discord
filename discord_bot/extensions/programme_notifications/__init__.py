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

# timestamp during the conference used for testing (see timewarm in config)
# general programme notifications are send 5 minutes before the session, and
# room notifications are send 2 minutes before the session
TIME_DURING_CONFERENCE = "2024-04-23T15:54:45+02:00"  # programme notification
# TIME_DURING_CONFERENCE = "2024-04-23T15:57:45+02:00"  # room notification


async def setup(bot: commands.Bot) -> None:
    """Set up the Programme Notifications extension."""
    client_session = _create_aiohttp_session()
    session_repository = repositories.SessionRepository()
    config = configuration.NotifierConfiguration.from_environment(root_configuration.Config())

    # Allow for time travel to conference days for test environments
    if config.timewarp:
        _logger.info("Time warping is enabled! Time traveling to the conference days.")
        now = arrow.now(tz=config.timezone)
        # Diff with some point in time during the conference
        diff = arrow.get(TIME_DURING_CONFERENCE) - now

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
    timeout = aiohttp.ClientTimeout(total=20)
    return aiohttp.ClientSession(
        connector=connector,
        headers={"User-Agent": "EP2023 Programme Notifier/2023.2"},
        raise_for_status=True,
        timeout=timeout,
    )
