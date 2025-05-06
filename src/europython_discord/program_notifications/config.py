from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class ProgramNotificationsConfig(BaseModel):
    timezone_offset: int
    api_url: str
    schedule_cache_file: Path
    livestream_url_file: Path
    main_notification_channel_name: str
    rooms_to_channel_names: Mapping[str, str]

    simulated_start_time: datetime | None = None
    fast_mode: bool = False
