from discord_bot.extensions.programme_notifications.domain import services
from tests.programme_notifications import factories


def test_filters_non_conference_days(
    session_factory: factories.SessionFactory, configuration_factory: factories.ConfigurationFactory
) -> None:
    """Only sessions held on conference days are relevant."""
    # GIVEN a config with start and end dates for the conference days
    config = configuration_factory(
        {
            "conference_days_first": "2023-07-19",
            "conference_days_last": "2023-07-21",
        }
    )
    # AND sessions both on and not on conference days
    sessions = [
        session_factory(id=1, submission={"code": "1"}, start="2023-07-21T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=2, submission={"code": "2"}, start="2023-07-20T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=3, submission={"code": "3"}, start="2023-07-21T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=4, submission={"code": "4"}, start="2023-07-18T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=5, submission={"code": "5"}, start="2023-07-18T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=6, submission={"code": "6"}, start="2023-07-19T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=7, submission={"code": "7"}, start="2021-07-20T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=8, submission={"code": "8"}, start="2023-07-17T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=9, submission={"code": "9"}, start="2023-07-23T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=10, submission={"code": "10"}, start="2023-07-22T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=11, submission={"code": "11"}, start="2023-07-20T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=12, submission={"code": "12"}, start="2023-07-19T09:11:12+02:00", room={"id": 1234}),
        session_factory(id=13, submission={"code": "13"}, start="2023-07-21T23:59:59+02:00", room={"id": 1234}),
    ]

    filtered_sessions = services.filter_conference_days(sessions, config)

    # THEN the filtered sessions are as expected
    expected_codes = ["1", "2", "3", "6", "11", "12", "13"]
    assert sorted((s.submission.code for s in filtered_sessions), key=lambda c: int(c)) == expected_codes
