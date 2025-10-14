"""Data structure for role IDs."""

import attrs


@attrs.define
class Roles:
    """Role mapping for the organisers extension."""

    organizers: int
    volunteers: int
    volunteers_onsite: int
    volunteers_remote: int
    sponsors: int
    speakers: int
    participants: int
    participants_onsite: int
    participants_remote: int
    supporter: int
