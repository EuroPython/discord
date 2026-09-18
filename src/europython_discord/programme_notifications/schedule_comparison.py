from datetime import date

from europython_discord.programme_notifications.models import ScheduleChange, Session


def build_session_lookup(schedule: dict[date, list[Session]]) -> dict[str, Session]:
    """Build a lookup dictionary for sessions by their code."""
    session_lookup = {}
    for sessions in schedule.values():
        for session in sessions:
            session_lookup[session.code] = session
    return session_lookup


def compare_schedules(
    old_schedule: dict[date, list[Session]], new_schedule: dict[date, list[Session]]
) -> list[ScheduleChange]:
    old_sessions = build_session_lookup(old_schedule)
    new_sessions = build_session_lookup(new_schedule)

    new_session_codes = new_sessions.keys() - old_sessions.keys()
    changes = []
    for session_code in new_session_codes:
        new_session = new_sessions[session_code]
        changes.append(ScheduleChange(old_session=None, new_session=new_session))
    cancelled_sessions = old_sessions.keys() - new_sessions.keys()
    for session_code in cancelled_sessions:
        old_session = old_sessions[session_code]
        changes.append(ScheduleChange(old_session=old_session, new_session=None))
    common_session_codes = old_sessions.keys() & new_sessions.keys()
    for session_code in common_session_codes:
        old_session = old_sessions[session_code]
        new_session = new_sessions[session_code]
        if (
            old_session.title != new_session.title
            or old_session.start != new_session.start
            or old_session.duration != new_session.duration
            or old_session.rooms != new_session.rooms
            or old_session.speakers != new_session.speakers
        ):
            changes.append(ScheduleChange(old_session=old_session, new_session=new_session))

    return changes
