from pathlib import Path

import pytest
from dotenv import load_dotenv

from EuroPythonBot.helpers.pretix_connector import get_roles

load_dotenv(Path("__file__").resolve().parent.parent.joinpath(".secrets"))

test_data = [
    ("TODOG GODOT", "RCZN9", ["Speakers", "Attendees"]),
    ("order 6 dog", "M09CT", ["Attendees"]),
    ("TBD TBD", "90LKW", ["Attendees"]),
    ("TODOG Talks No EMu", "30QNE", ["Speakers", "Attendees"]),
    ("Raquel Individual", "C0MV7", ["Attendees"]),
    ("Raquel Individual", "G0CFM", ["Attendees"]),
    ("order 2 dog", "M09CT", ["Attendees"]),
    ("Dog TBD", "90LKW", ["Attendees"]),
    ("order 3 dog", "M09CT", ["Attendees"]),
    ("order 4 dog", "M09CT", ["Attendees"]),
    ("order 5 dog", "M09CT", ["Attendees"]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("name,order,ticket_type", test_data)
async def test_should_return_ticket_type(name, order, ticket_type):
    assert await get_roles(name=name, order=order) == ticket_type
