import string
from dataclasses import dataclass

from unidecode import unidecode


def generate_ticket_key(*, order: str, name: str) -> str:
    # convert to ascii string (remove accents, split digraphs, ...)
    name = unidecode(name)

    # convert to lowercase, remove spaces and punctuation
    name = name.lower()
    name = "".join(c for c in name if not c.isspace())
    name = "".join(c for c in name if c not in string.punctuation)

    return f"{order.upper()}-{name}"


@dataclass(frozen=True)
class Ticket:
    order: str
    name: str
    type: str

    @property
    def key(self) -> str:
        return generate_ticket_key(order=self.order, name=self.name)
