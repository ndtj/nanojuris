"""Small in-process circuit breaker isolated per provider operation."""

from __future__ import annotations

import time
from collections.abc import Callable
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Trip after consecutive transport failures and recover after a cooldown."""

    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        reset_timeout: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1 or reset_timeout < 0:
            raise ValueError("invalid circuit breaker limits")
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._clock = clock
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        if self._state is CircuitState.OPEN and self._opened_at is not None:
            if self._clock() - self._opened_at >= self.reset_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def failures(self) -> int:
        return self._failures

    def allow(self) -> bool:
        return self.state is not CircuitState.OPEN

    def record_success(self) -> None:
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._state is CircuitState.HALF_OPEN or self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = self._clock()

    def reset(self) -> None:
        self.record_success()
