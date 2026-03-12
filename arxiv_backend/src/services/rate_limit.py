"""
Redis-backed rate limiter: global, per-IP, and per-user limits using fixed windows.
"""

import time
from typing import Optional

import redis
from arxiv_lib.config import RedisSettings
from loguru import logger

# Lua: INCR key, set EXPIRE on first request in window, return count.
# KEYS[1] = key, ARGV[1] = window_seconds
LUA_INCR_WINDOW = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return n
"""


class RateLimiter:
    """Redis-based rate limiter with global, IP, and user buckets."""

    PREFIX_GLOBAL = "rl:g:"
    PREFIX_IP = "rl:i:"
    PREFIX_USER = "rl:u:"

    def __init__(self, redis_client: redis.Redis, settings: RedisSettings):
        self.redis = redis_client
        self.settings = settings
        self.window = settings.rate_limit_window_seconds
        self._script = redis_client.register_script(LUA_INCR_WINDOW)

    def _window_key(self) -> int:
        """Current fixed window (e.g. minute id)."""
        return int(time.time() // self.window)

    def _incr_and_get(self, key: str) -> int:
        """Atomically increment counter for key and return new count."""
        try:
            full_key = f"{key}{self._window_key()}"
            return self._script(keys=[full_key], args=[self.window * 2])
        except Exception as e:
            logger.warning("Rate limit Redis error, allowing request: {}", e)
            return 0

    def check_global(self) -> Optional[str]:
        """
        Check global limit. Returns None if allowed, or error message if exceeded.
        """
        key = f"{self.PREFIX_GLOBAL}"
        count = self._incr_and_get(key)
        if count > self.settings.rate_limit_global:
            return "Global rate limit exceeded. Try again later."

        return None

    def check_ip(self, ip: str) -> Optional[str]:
        """
        Check per-IP limit. Returns None if allowed, or error message if exceeded.
        """
        if not ip or not ip.strip():
            return None
        key = f"{self.PREFIX_IP}{ip}:"
        count = self._incr_and_get(key)
        if count > self.settings.rate_limit_per_ip:
            return "Too many requests from this IP. Try again later."

        return None

    def check_user(self, user_id: str) -> Optional[str]:
        """
        Check per-user limit. Returns None if allowed, or error message if exceeded.
        """
        if not user_id or not str(user_id).strip():
            return None
        key = f"{self.PREFIX_USER}{user_id}:"
        count = self._incr_and_get(key)
        if count > self.settings.rate_limit_per_user:
            return "User rate limit exceeded. Try again later."

        return None

    def check(self, ip: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Run global, then IP, then user checks. Returns first error message or None.
        """
        err = self.check_global()
        if err:
            return err
        err = self.check_ip(ip)
        if err:
            return err
        if user_id is not None:
            err = self.check_user(str(user_id))
            if err:
                return err
        return None
