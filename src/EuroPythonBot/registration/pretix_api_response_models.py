from __future__ import annotations

import pydantic


class PretixItem(pydantic.BaseModel):
    """Item which can be ordered, e.g. 'Business', 'Personal', 'Education'."""

    # https://docs.pretix.eu/en/latest/api/resources/items.html
    id: int
    names_by_locale: dict[str, str] = pydantic.Field(alias="name")
    variations: list[PretixItemVariation]


class PretixItemVariation(pydantic.BaseModel):
    """Variation of item, e.g. 'Conference', 'Tutorial', 'Volunteer'."""

    # https://docs.pretix.eu/en/latest/api/resources/item_variations.html
    id: int
    names_by_locale: dict[str, str] = pydantic.Field(alias="value")


class PretixOrder(pydantic.BaseModel):
    """Order containing one or more positions."""

    # https://docs.pretix.eu/en/latest/api/resources/orders.html#order-resource
    id: str = pydantic.Field(alias="code")
    status: str
    positions: list[PretixOrderPosition]

    @property
    def is_paid(self) -> bool:
        # n: pending, p: paid, e: expired, c: canceled
        return self.status == "p"


class PretixOrderPosition(pydantic.BaseModel):
    """Ordered position, e.g. a ticket or a T-shirt."""

    # https://docs.pretix.eu/en/latest/api/resources/orders.html#order-position-resource
    order_id: str = pydantic.Field(alias="order")
    item_id: int = pydantic.Field(alias="item")
    variation_id: int | None = pydantic.Field(alias="variation")
    attendee_name: str | None
