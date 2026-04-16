from dataclasses import dataclass
from time import monotonic


@dataclass
class CircuitBreakerState:
    name: str
    state: str
    failure_count: int


class CircuitBreakerOpenError(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: int = 30,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.failure_count = 0
        self.opened_at: float | None = None
        self.state = "closed"

    def before_call(self) -> None:
        if self.state != "open":
            return

        if self.opened_at is None:
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        elapsed = monotonic() - self.opened_at
        if elapsed >= self.recovery_timeout_seconds:
            self.state = "half-open"
            return

        raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None
        self.state = "closed"

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.opened_at = monotonic()

    def snapshot(self) -> CircuitBreakerState:
        return CircuitBreakerState(
            name=self.name,
            state=self.state,
            failure_count=self.failure_count,
        )
