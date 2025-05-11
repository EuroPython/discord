from __future__ import annotations

import string

from pydantic import BaseModel, ConfigDict, computed_field
from unidecode import unidecode


def generate_ticket_key(*, order: str, name: str) -> str:
    # convert to ascii string (remove accents, split digraphs, ...)
    name = unidecode(name)

    # convert to lowercase, remove spaces and punctuation
    name = name.lower()
    name = "".join(c for c in name if not c.isspace())
    name = "".join(c for c in name if c not in string.punctuation)

    return f"{order}-{name}"


class Ticket(BaseModel):
    model_config = ConfigDict(frozen=True)

    order: str
    name: str
    type: str
    variation: str | None

    @computed_field
    def key(self) -> str:
        return generate_ticket_key(order=self.order, name=self.name)
