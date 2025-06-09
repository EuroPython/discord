from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from pydantic import AwareDatetime, BaseModel


class ProgramNotificationsConfig(BaseModel):
    api_url: str
    schedule_cache_file: Path
    livestream_url_file: Path
    main_notification_channel_name: str
    rooms_to_channel_names: Mapping[str, str]

    simulated_start_time: AwareDatetime | None = None
    fast_mode: bool = False
