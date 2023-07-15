from tests.programme_notifications import factories

from extensions.programme_notifications.domain import services


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
        session_factory(code="1", slot={"start": "2023-07-21T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="2", slot={"start": "2023-07-20T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="3", slot={"start": "2023-07-21T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="4", slot={"start": "2023-07-18T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="5", slot={"start": "2023-07-18T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="6", slot={"start": "2023-07-19T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="7", slot={"start": "2021-07-20T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="8", slot={"start": "2023-07-17T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="9", slot={"start": "2023-07-23T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="10", slot={"start": "2023-07-22T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="11", slot={"start": "2023-07-20T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="12", slot={"start": "2023-07-19T09:11:12+02:00", "room_id": 1234}),
        session_factory(code="13", slot={"start": "2023-07-21T23:59:59+02:00", "room_id": 1234}),
    ]

    filtered_sessions = services.filter_conference_days(sessions, config)

    # THEN the filtered sessions are as expected
    expected_codes = ["1", "2", "3", "6", "11", "12", "13"]
    assert sorted((s.code for s in filtered_sessions), key=lambda c: int(c)) == expected_codes
