from __future__ import annotations

import logging
import time

_logger = logging.getLogger(__name__)

DUCK_API_URL = "https://random-d.uk/api/randomimg"


class DuckClient:
    def __init__(self) -> None:
        pass

    async def fetch_random_duck(self) -> str | None:
        # Since the API directly returns the image and we don't need to parse JSON,
        # we can just return the URL with a cache-busting timestamp so Discord fetches a new one.
        # Alternatively, if we wanted to verify it's up, we could do a HEAD request.
        # For simplicity and performance, we'll just return the URL.
        timestamp = int(time.time() * 1000)
        return f"{DUCK_API_URL}?t={timestamp}"
