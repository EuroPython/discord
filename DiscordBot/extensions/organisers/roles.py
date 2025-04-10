"""Data structure for role IDs."""
import attrs


@attrs.define
class Roles:
    """Role mapping for the organisers extension."""

    organisers: int
    volunteers: int
    volunteers_remote: int
    speakers: int
    sponsors: int
    attendee: int
    onsite: int
    remote: int
