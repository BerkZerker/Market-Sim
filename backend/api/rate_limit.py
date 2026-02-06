import time
from uuid import UUID

from config import settings
from fastapi import HTTPException, status


class RateLimiter:
    """Sliding window rate limiter keyed by user ID."""

    def __init__(
        self,
        max_requests: int = settings.RATE_LIMIT_REQUESTS,
        window_seconds: int = settings.RATE_LIMIT_WINDOW,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[UUID, list[float]] = {}

    def check(self, user_id: UUID) -> None:
        now = time.monotonic()
        timestamps = self._requests.get(user_id, [])
        cutoff = now - self.window_seconds
        timestamps = [t for t in timestamps if t > cutoff]
        if len(timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )
        timestamps.append(now)
        self._requests[user_id] = timestamps


_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _limiter
