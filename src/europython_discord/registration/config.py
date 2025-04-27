from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel


class RegistrationConfig(BaseModel):
    # discord
    registration_form_channel_name: str
    registration_help_channel_name: str
    registration_log_channel_name: str

    # pretix
    pretix_base_url: str
    item_to_roles: Mapping[str, Sequence[str]]
    variation_to_roles: Mapping[str, Sequence[str]]

    # cache files
    pretix_cache_file: Path
    registered_cache_file: Path
