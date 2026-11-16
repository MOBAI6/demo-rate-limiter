"""Token Bucket Rate Limiter Implementation Module."""

import threading
import time
from typing import Union

from rate_limiter import RateLimiter


class TokenBucketLimiter(RateLimiter):
    """Thread-safe Token Bucket Rate Limiter implementation.

    Attributes:
        capacity: Maximum capacity of the token bucket.
        refill_rate: Rate at which tokens are added per second.
    """

    def __init__(self, capacity: Union[int, float], refill_rate: Union[int, float]) -> None:
        """Initialize the token bucket rate limiter.

        Args:
            capacity: Maximum number of tokens the bucket can hold (must be > 0).
            refill_rate: Number of tokens added per second (must be > 0).

        Raises:
            ValueError: If capacity or refill_rate is not positive.
        """
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        if refill_rate <= 0:
            raise ValueError(f"refill_rate must be positive, got {refill_rate}")

        self._capacity: float = float(capacity)
        self._refill_rate: float = float(refill_rate)
        self._tokens: float = float(capacity)
        self._last_refill_ns: int = time.monotonic_ns()
        self._lock: threading.Lock = threading.Lock()

    @property
    def capacity(self) -> float:
        """Return the maximum token capacity."""
        return self._capacity

    @property
    def refill_rate(self) -> float:
        """Return the refill rate in tokens per second."""
        return self._refill_rate

    @property
    def current_tokens(self) -> float:
        """Return current available tokens after dynamic refill (thread-safe)."""
        with self._lock:
            self._refill_locked()
            return self._tokens

    def _refill_locked(self) -> None:
        """Refill tokens based on elapsed nanoseconds.

        Note:
            Must be called while holding self._lock.
        """
        now_ns: int = time.monotonic_ns()
        elapsed_ns: int = now_ns - self._last_refill_ns
        if elapsed_ns > 0:
            added_tokens: float = (elapsed_ns / 1_000_000_000.0) * self._refill_rate
            self._tokens = min(self._capacity, self._tokens + added_tokens)
            self._last_refill_ns = now_ns

    def allow_request(self, tokens: int = 1) -> bool:
        """Check if request consuming tokens is allowed and consume if permitted.

        Args:
            tokens: Number of tokens required for the request. Defaults to 1.

        Returns:
            bool: True if sufficient tokens exist and were consumed, False otherwise.

        Raises:
            ValueError: If tokens requested is negative.
        """
        if tokens < 0:
            raise ValueError(f"tokens must be non-negative, got {tokens}")
        if tokens == 0:
            return True

        with self._lock:
            self._refill_locked()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
