from __future__ import annotations

import logging
import time

_logger = logging.getLogger(__name__)

DUCK_API_URL = "https://random-d.uk/api/randomimg"


class DuckClient:
    def __init__(self) -> None:
        pass

    async def fetch_random_duck(self) -> str | None:
        # Get a random duck image from random-d.uk
        timestamp = int(time.time() * 1000)
        return f"{DUCK_API_URL}?t={timestamp}"
