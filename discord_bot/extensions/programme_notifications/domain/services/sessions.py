"""Manipulate iterables of EuroPython sessions."""

import collections
from collections.abc import Iterator
from typing import Iterable, TypeAlias

import arrow

from discord_bot.extensions.programme_notifications import configuration
from discord_bot.extensions.programme_notifications.domain import europython

GroupedSessions: TypeAlias = collections.defaultdict[arrow.Arrow, list[europython.Session]]


def group_sessions_by_minutes(sessions: Iterable[europython.Session]) -> GroupedSessions:
    """Group the sessions by their start time in minutes.

    If sessions do not have a start time, they will be ignored.

    :param sessions: The sessions to group
    :return: A dictionary mapping an `arrow.Arrow` to all sessions that
      start at that time.
    """
    grouped_sessions: GroupedSessions = collections.defaultdict(list)
    for session in sessions:
        try:
            start_time = session.slot.start.floor("minutes")
        except AttributeError:
            continue
        grouped_sessions[start_time].append(session)
    return grouped_sessions


def filter_conference_days(
    sessions: Iterable[europython.Session],
    config: configuration.NotifierConfiguration,
) -> Iterator[europython.Session]:
    """Yield only sessions that are held on conference days."""
    first_day = config.conference_days_first.replace(tzinfo=config.timezone).floor("day")
    last_day = config.conference_days_last.replace(tzinfo=config.timezone).ceil("day")
    for session in sessions:
        if session.slot.start.is_between(first_day, last_day, "[]"):
            yield session
