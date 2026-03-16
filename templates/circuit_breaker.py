"""
Circuit Breaker: Za kriticne external API pozive (payment, auth)
Usage:
    cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0, name="stripe")
    result = await cb.call(stripe_api.charge, amount=1000)
"""
import time
import logging
from enum import Enum
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0, name: str = "default") -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count: int = 0
        self.success_count: int = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: float = 0

    async def call(self, fn: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit '{self.name}' HALF_OPEN, testing recovery")
            else:
                raise CircuitOpenError(f"Circuit '{self.name}' OPEN, retry after {self.recovery_timeout}s")
        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self.failure_count = 0
        self.success_count += 1
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit '{self.name}' recovered, CLOSED")
        self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit '{self.name}' OPEN after {self.failure_count} failures")

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failure_count,
            "successes": self.success_count,
        }
