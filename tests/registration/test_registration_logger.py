from pathlib import Path

import pytest

from registration.registration_logger import RegistrationLogger
from registration.ticket import Ticket


def test_with_empty_file(tmp_path: Path) -> None:
    logger = RegistrationLogger(tmp_path / "registrations.txt")

    assert not logger.is_registered(
        Ticket(order="ABC01", name="John Doe", type="Business", variation="Tutorials")
    )


def test_with_existing_file(tmp_path: Path) -> None:
    (tmp_path / "registrations.txt").write_text("ABC01-johndoe\n")

    logger = RegistrationLogger(tmp_path / "registrations.txt")

    assert logger.is_registered(
        Ticket(order="ABC01", name="John Doe", type="Business", variation="Tutorials")
    )


@pytest.mark.asyncio
async def test_register_ticket_on_empty_log(tmp_path: Path) -> None:
    logger = RegistrationLogger(tmp_path / "registrations.txt")

    ticket = Ticket(order="ABC01", name="John Doe", type="Business", variation="Tutorials")

    await logger.mark_as_registered(ticket)

    assert logger.is_registered(ticket)
    assert (tmp_path / "registrations.txt").read_text() == "ABC01-johndoe\n"


@pytest.mark.asyncio
async def test_register_ticket_with_existing_file(tmp_path: Path) -> None:
    logger = RegistrationLogger(tmp_path / "registrations.txt")

    ticket = Ticket(order="ABC01", name="John Doe", type="Business", variation="Tutorials")

    await logger.mark_as_registered(ticket)

    assert logger.is_registered(ticket)
    assert (tmp_path / "registrations.txt").read_text() == "ABC01-johndoe\n"


@pytest.mark.asyncio
async def test_register_ticket_with_existing_log(tmp_path: Path) -> None:
    (tmp_path / "registrations.txt").write_text("ABC01-johndoe\n")

    logger = RegistrationLogger(tmp_path / "registrations.txt")

    ticket = Ticket(order="ABC02", name="Jane Doe", type="Business", variation="Tutorials")

    await logger.mark_as_registered(ticket)

    assert logger.is_registered(ticket)
    assert (tmp_path / "registrations.txt").read_text() == "ABC01-johndoe\nABC02-janedoe\n"


@pytest.mark.asyncio
async def test_register_already_registered_ticket(tmp_path: Path) -> None:
    logger = RegistrationLogger(tmp_path / "registrations.txt")

    ticket = Ticket(order="ABC02", name="Jane Doe", type="Business", variation="Tutorials")

    await logger.mark_as_registered(ticket)

    with pytest.raises(ValueError, match="already registered"):
        await logger.mark_as_registered(ticket)
