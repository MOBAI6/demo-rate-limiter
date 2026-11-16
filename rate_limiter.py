"""Rate Limiter Abstract Base Class Module."""

from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """Abstract base class defining the interface for rate limiters."""

    @abstractmethod
    def allow_request(self, tokens: int = 1) -> bool:
        """Check if a request consuming the specified number of tokens is allowed.

        Args:
            tokens: Number of tokens required for the request. Defaults to 1.

        Returns:
            bool: True if the request is permitted within rate limits, False otherwise.
        """
        raise NotImplementedError
