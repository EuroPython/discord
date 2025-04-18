"""Data structure for role IDs."""

import attrs


@attrs.define
class Roles:
    """Role mapping for the admin extension."""

    organiser: int
    volunteer: int
    attendee: int
    speaker: int
    session_chair: int
    sponsor: int
    on_site: int
    remote: int
