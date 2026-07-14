from __future__ import annotations

import time


class RateLimiter:
    """Utility class to prevent users from using a resource too frequently."""

    def __init__(self, cooldown_seconds: float) -> None:
        self._last_usage_by_user_id: dict[int, float] = {}
        self._cooldown_seconds = cooldown_seconds

    def is_rate_limited(self, user_id: int) -> bool:
        last_usage = self._last_usage_by_user_id.get(user_id, 0)
        timeout_end = last_usage + self._cooldown_seconds
        return self.get_current_timestamp() < timeout_end

    def get_seconds_until_cooldown(self, user_id: int) -> float:
        last_usage = self._last_usage_by_user_id.get(user_id, 0)
        timeout_end = last_usage + self._cooldown_seconds
        return max(0, timeout_end - self.get_current_timestamp())

    def register_usage(self, user_id: int) -> None:
        self._last_usage_by_user_id[user_id] = self.get_current_timestamp()

    @staticmethod
    def get_current_timestamp() -> float:
        return time.time()
