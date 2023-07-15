import arrow
import pytest
from tests.programme_notifications import factories

from extensions.programme_notifications.domain import europython, services


@pytest.mark.parametrize(
    ("sessions", "expected_groups"),
    [
        pytest.param([], {}, id="no session"),
        pytest.param(
            [
                {
                    "code": "ABCDEF",
                    "slot": {"room_id": 1234, "start": "2023-07-19T09:55:00+02:00"},
                },
            ],
            {arrow.Arrow(2023, 7, 19, 9, 55, 0, tzinfo="Europe/Prague"): ["ABCDEF"]},
            id="one session",
        ),
        pytest.param(
            [
                {
                    "code": "ABCDEF",
                    "slot": {"room_id": 1234, "start": "2023-07-19T10:55:00+02:00"},
                },
                {
                    "code": "123456",
                    "slot": {"room_id": 1234, "start": "2023-07-19T08:55:00+00:00"},
                },
            ],
            {arrow.Arrow(2023, 7, 19, 10, 55, 0, tzinfo="Europe/Prague"): ["ABCDEF", "123456"]},
            id="two sessions, same start minute",
        ),
        pytest.param(
            [
                {
                    "code": "ABCDEF",
                    "slot": {"room_id": 1234, "start": "2023-07-19T09:55:00+02:00"},
                },
                {
                    "code": "123456",
                    "slot": {"room_id": 1234, "start": "2023-07-19T08:55:00+01:00"},
                },
                {
                    "code": "ZZZEEE",
                    "slot": {"room_id": 1234, "start": "2023-07-19T11:55:00+01:00"},
                },
            ],
            {
                arrow.Arrow(2023, 7, 19, 9, 55, 0, tzinfo="Europe/Prague"): ["ABCDEF", "123456"],
                arrow.Arrow(2023, 7, 19, 12, 55, 0, tzinfo="Europe/Prague"): ["ZZZEEE"],
            },
            id="two groups",
        ),
    ],
    indirect=["sessions"],
)
def test_grouper_groups_sessions_per_minute(
    sessions: list[europython.Session],
    expected_groups: dict[arrow.Arrow, str],
    session_factory: factories.SessionFactory,
) -> None:
    """Groups help with sending combined programme notifications."""
    # GIVEN a list of sessions
    # WHEN the sessions are grouped
    grouped_sessions = services.group_sessions_by_minutes(sessions)

    # THEN the number of groups matches the expected groups
    assert len(grouped_sessions) == len(expected_groups)
    # AND the group keys match the expected group keys
    assert all(key in expected_groups for key in grouped_sessions)
    # AND the sessions in the groups are as expected
    for key, group in grouped_sessions.items():
        assert sorted(s.code for s in group) == sorted(expected_groups[key])
