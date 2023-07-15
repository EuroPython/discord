from unittest import mock

import yarl
from tests.programme_notifications import factories
from tests.programme_notifications.services import helpers

from extensions.programme_notifications import services
from extensions.programme_notifications.domain import discord, europython, repositories
from extensions.programme_notifications.services import api, clock, task_scheduler


async def test_does_not_schedule_tasks_for_schedule_without_session(
    client_session: mock.Mock, configuration_factory: factories.ConfigurationFactory
) -> None:
    """There are no notifications without sessions."""
    # GIVEN a schedule with no sessions
    schedule = europython.Schedule(
        sessions=[],
        version="0.1.0",
        schedule_hash="9f31a9974e4fb907c2a553a73d306bcae9212e4f",
        breaks=[],
    )
    # GIVEN a fake api client that returns the schedule
    client = mock.create_autospec(api.IApiClient)
    client.fetch_schedule.return_value = schedule
    # AND an instance of the config
    config = configuration_factory({})
    # AND an instance of the session information service
    session_info = services.SessionInformation(
        session_repository=repositories.SessionRepository(), api_client=client, config=config
    )
    # AND a task scheduler mock
    scheduler = mock.create_autospec(spec=task_scheduler.IScheduler)
    # AND a notifier that uses that client
    notifier = services.Notifier(
        api_client=client, config=config, session_information=session_info, scheduler=scheduler
    )

    # WHEN notifications are scheduled
    await notifier.schedule_notifications()

    # THEN no notifications were scheduled
    scheduler.schedule_tasks_at.assert_not_called()


async def test_scheduling_notifications_delivers_to_webhooks(
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
    session_factory: factories.SessionFactory,
) -> None:
    """The notifier schedules the correct number of tasks."""
    # GIVEN a single session session
    sessions = {
        "ABCDEF": session_factory(
            **{
                "code": "ABCDEF",
                "title": "Feeding Your Pet Python",
                "abstract": "Pythons need to eat, too!",
                "track": {"en": "Pet Pythons"},
                "duration": 37,
                "slot": {
                    "room_id": 1234,
                    "room": {"en": "The Main Terrarium"},
                    "start": "2023-07-19T09:55:00+02:00",
                },
                "speakers": [
                    {"code": "BBCDEE", "name": "Monty the Python", "avatar": "https://snek.com"}
                ],
            }
        )
    }
    # AND a schedule with only that session
    schedule = europython.Schedule(
        sessions=list(sessions.values()),
        version="0.1.0",
        schedule_hash="9f31a9974e4fb907c2a553a73d306bcae9212e4f",
        breaks=[],
    )
    # AND an api client that returns the schedule and session details
    client = mock.create_autospec(api.IApiClient)
    client.fetch_schedule.return_value = schedule
    session_details = {
        "ABCDEF": (yarl.URL("https://europythoon/hungry-snakes"), "intermediate"),
    }
    client.fetch_session_details.side_effect = lambda session_code: session_details[session_code]
    # AND an instance of the config
    config = configuration_factory(
        {
            "rooms": {
                "1234": {
                    "discord_channel_id": "1234567890",
                    "webhook_id": "room_1234",
                    "livestreams": {
                        "2023-07-19": "https://one.livestream.ep",
                        "2023-07-20": "https://two.livestream.ep",
                        "2023-07-21": "https://three.livestream.ep",
                    },
                }
            },
            "webhooks": {
                "schedule_notifications_one": yarl.URL("https://one.webhook.ep"),
                "schedule_notifications_two": yarl.URL("https://two.webhook.ep"),
            },
            "notification_channels": [
                {"webhook_id": "schedule_notifications_one", "include_channel_in_embeds": True},
                {"webhook_id": "schedule_notifications_two", "include_channel_in_embeds": False},
            ],
        }
    )
    # AND a session information service with the session
    session_info = services.SessionInformation(
        session_repository=repositories.SessionRepository(),
        api_client=client,
        config=config,
    )
    # AND a clock with a know `now` and fake sleeper
    clock_obj = clock.Clock(sleeper=mock.AsyncMock())
    # AND a scheduler that uses that clock
    scheduler = helpers.AwaitableScheduler(clock=clock_obj)
    # AND a notifier that uses that client
    notifier = services.Notifier(
        api_client=client,
        config=config,
        session_information=session_info,
        scheduler=scheduler,
    )

    # WHEN notifications are scheduled
    await notifier.schedule_notifications()
    await scheduler.wait_until_completed()

    # THEN three notifications were sent
    assert client.execute_webhook.await_count == 3
    # AND a notification was sent to the first notification channel
    first_notification_channel_call = mock.call(
        discord.WebhookMessage(
            content="# Sessions starting in 5 minutes:",
            embeds=[
                discord.Embed(
                    title="Feeding Your Pet Python",
                    author=discord.Author(name="Monty the Python", icon_url="https://snek.com"),
                    description=(
                        "Pythons need to eat, too!\n\n"
                        "[Read more about this session](https://europythoon/hungry-snakes)"
                    ),
                    fields=[
                        discord.Field(name="Start Time", value="<t:1689753300:f>", inline=True),
                        discord.Field(name="Room", value="The Main Terrarium", inline=True),
                        discord.Field(name="Track", value="Pet Pythons", inline=True),
                        discord.Field(name="Duration", value="37 minutes", inline=True),
                        discord.Field(
                            name="Livestream",
                            value="[YouTube](https://one.livestream.ep)",
                            inline=True,
                        ),
                        discord.Field(name="Discord Channel", value="<#1234567890>", inline=True),
                    ],
                    footer=discord.Footer(
                        text="This session starts at 09:55:00 (local conference time)"
                    ),
                    url="https://europythoon/hungry-snakes",
                    color=16764229,
                )
            ],
        ),
        webhook="schedule_notifications_one",
    )
    assert first_notification_channel_call in client.execute_webhook.await_args_list
    # AND a notification was sent to the second notification channel
    second_notification_channel_call = mock.call(
        discord.WebhookMessage(
            content="# Sessions starting in 5 minutes:",
            embeds=[
                discord.Embed(
                    title="Feeding Your Pet Python",
                    author=discord.Author(name="Monty the Python", icon_url="https://snek.com"),
                    description=(
                        "Pythons need to eat, too!\n\n"
                        "[Read more about this session](https://europythoon/hungry-snakes)"
                    ),
                    fields=[
                        discord.Field(name="Start Time", value="<t:1689753300:f>", inline=True),
                        discord.Field(name="Room", value="The Main Terrarium", inline=True),
                        discord.Field(name="Track", value="Pet Pythons", inline=True),
                        discord.Field(name="Duration", value="37 minutes", inline=True),
                        discord.Field(
                            name="Livestream",
                            value="[YouTube](https://one.livestream.ep)",
                            inline=True,
                        ),
                        discord.Field(name="Level", value="Intermediate", inline=True),
                    ],
                    footer=discord.Footer(
                        text="This session starts at 09:55:00 (local conference time)"
                    ),
                    url="https://europythoon/hungry-snakes",
                    color=16764229,
                )
            ],
        ),
        webhook="schedule_notifications_two",
    )
    assert second_notification_channel_call in client.execute_webhook.await_args_list
    # AND the room notification call is in the await calls list
    room_notification_call = mock.call(
        discord.WebhookMessage(
            content="# Next up in this room:",
            embeds=[
                discord.Embed(
                    title="Feeding Your Pet Python",
                    author=discord.Author(name="Monty the Python", icon_url="https://snek.com"),
                    description=(
                        "Pythons need to eat, too!\n\n"
                        "[Read more about this session](https://europythoon/hungry-snakes)"
                    ),
                    fields=[
                        discord.Field(name="Start Time", value="<t:1689753300:f>", inline=True),
                        discord.Field(name="Room", value="The Main Terrarium", inline=True),
                        discord.Field(name="Track", value="Pet Pythons", inline=True),
                        discord.Field(name="Duration", value="37 minutes", inline=True),
                        discord.Field(
                            name="Livestream",
                            value="[YouTube](https://one.livestream.ep)",
                            inline=True,
                        ),
                        discord.Field(name="Level", value="Intermediate", inline=True),
                    ],
                    footer=discord.Footer(
                        text="This session starts at 09:55:00 (local conference time)"
                    ),
                    url="https://europythoon/hungry-snakes",
                    color=16764229,
                )
            ],
        ),
        webhook="room_1234",
    )
    assert room_notification_call in client.execute_webhook.await_args_list


async def test_does_not_schedule_tasks_if_schedule_has_not_changed(
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
    session_factory: factories.SessionFactory,
) -> None:
    """Only refresh the notifications if the schedule has changed!"""
    # GIVEN two sessions
    sessions = {"ABCDEF": session_factory(code="ABCDEF"), "FEDCBA": session_factory(code="FEDCBA")}
    # AND a schedule with only that session
    schedule = europython.Schedule(
        sessions=list(sessions.values()),
        version="0.1.0",
        schedule_hash="9f31a9974e4fb907c2a553a73d306bcae9212e4f",
        breaks=[],
    )
    # AND an api client that returns the schedule and session details
    client = mock.create_autospec(api.IApiClient)
    client.fetch_schedule.return_value = schedule
    client.fetch_session_details.return_value = (
        yarl.URL("https://europythoon/my-slug"),
        "intermediate",
    )
    # AND an instance of the config
    config = configuration_factory({})
    # AND a session information service
    session_info = services.SessionInformation(
        session_repository=repositories.SessionRepository(),
        api_client=client,
        config=config,
    )
    # AND a task scheduler mock
    scheduler = mock.create_autospec(spec=task_scheduler.IScheduler)
    scheduler.schedule_tasks_at.side_effect = lambda *coros, at: [c.close() for c in coros]
    # AND a notifier with a previous schedule hash equal to the new hash
    notifier = services.Notifier(
        api_client=client,
        config=config,
        session_information=session_info,
        scheduler=scheduler,
    )
    # AND the notifications tasks are scheduled a first time
    await notifier.schedule_notifications()
    scheduler.reset_mock()

    # WHEN they are scheduled again with the same schedule
    await notifier.schedule_notifications()

    # THEN pending tasks were not cancelled
    scheduler.cancel_all.assert_not_called()
    # AND no new schedule calls were made
    assert scheduler.schedule_tasks_at.call_count == 0


async def test_force_bypasses_hash_check(
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
    session_factory: factories.SessionFactory,
) -> None:
    """Even if the schedule hasn't changed, allow for manual refresh."""
    # GIVEN two sessions
    sessions = {"ABCDEF": session_factory(code="ABCDEF"), "FEDCBA": session_factory(code="FEDCBA")}
    # AND a schedule with those sessions
    schedule = europython.Schedule(
        sessions=list(sessions.values()),
        version="0.1.0",
        schedule_hash="9f31a9974e4fb907c2a553a73d306bcae9212e4f",
        breaks=[],
    )
    # AND an api client that returns the schedule and session details
    client = mock.create_autospec(api.IApiClient)
    client.fetch_schedule.return_value = schedule
    client.fetch_session_details.return_value = (
        yarl.URL("https://europythoon/my-slug"),
        "intermediate",
    )
    # AND an instance of the config
    config = configuration_factory({})
    # AND a session information service
    session_info = services.SessionInformation(
        session_repository=repositories.SessionRepository(),
        api_client=client,
        config=config,
    )
    # AND a task scheduler mock
    scheduler = mock.create_autospec(spec=task_scheduler.IScheduler)
    scheduler.schedule_tasks_at.side_effect = lambda *coros, at: [c.close() for c in coros]
    # AND a notifier with a previous schedule hash equal to the new hash
    notifier = services.Notifier(
        api_client=client,
        config=config,
        session_information=session_info,
        scheduler=scheduler,
    )
    # AND the notifications tasks are scheduled a first time
    await notifier.schedule_notifications()
    scheduler.reset_mock()

    # WHEN the sessions are scheduled again
    await notifier.schedule_notifications(force=True)

    # THEN the pending notifications were cancelled
    scheduler.cancel_all.assert_called_once()
    # AND the new notifications were scheduled
    assert scheduler.schedule_tasks_at.call_count == 2


async def test_excludes_non_conference_days_sessions(
    client_session: mock.Mock,
    configuration_factory: factories.ConfigurationFactory,
    session_factory: factories.SessionFactory,
) -> None:
    """Only provide notifications for sessions on conference days."""
    # GIVEN two sessions that fall outside the conference days
    sessions = {
        "ABCDEF": session_factory(
            **{
                "code": "ABCDEF",
                "title": "Feeding Your Pet Python",
                "abstract": "Pythons need to eat, too!",
                "track": {"en": "Pet Pythons"},
                "duration": 37,
                "slot": {
                    "room_id": 1234,
                    "room": {"en": "The Main Terrarium"},
                    "start": "2021-07-18T23:59:59+02:00",
                },
                "speakers": [
                    {"code": "BBCDEE", "name": "Monty the Python", "avatar": "https://snek.com"}
                ],
            }
        ),
        "GHIJKL": session_factory(
            **{
                "code": "GHIJKL",
                "title": "The Airspeed of an Unladen Swallow",
                "abstract": "It's 50 – 65 km/h",
                "track": {"en": "Birds"},
                "duration": 11,
                "slot": {
                    "room_id": 1234,
                    "room": {"en": "The Main Terrarium"},
                    "start": "2021-07-22T00:00:00+02:00",
                },
                "speakers": [
                    {"code": "BBCDEE", "name": "Monty the Python", "avatar": "https://snek.com"}
                ],
            }
        ),
    }
    # AND a schedule with only those sessions
    schedule = europython.Schedule(
        sessions=list(sessions.values()),
        version="0.1.0",
        schedule_hash="9f31a9974e4fb907c2a553a73d306bcae9212e4f",
        breaks=[],
    )
    # AND an api client that returns the schedule and session details
    client = mock.create_autospec(api.IApiClient)
    client.fetch_schedule.return_value = schedule
    # AND config that states the sessions are outside of conference days
    config = configuration_factory(
        {
            "conference_days_first": "2021-07-19",
            "conference_days_last": "2021-07-21",
        }
    )
    # AND a session information service
    session_info = services.SessionInformation(
        session_repository=repositories.SessionRepository(),
        api_client=client,
        config=config,
    )
    # AND a task scheduler mock
    scheduler = mock.create_autospec(spec=task_scheduler.IScheduler)
    # AND a notifier that uses that client
    notifier = services.Notifier(
        api_client=client, config=config, session_information=session_info, scheduler=scheduler
    )

    # WHEN notifications are scheduled based on the schedule
    await notifier.schedule_notifications()

    # THEN no notifications were actually scheduled
    scheduler.schedule_tasks_at.assert_not_called()
