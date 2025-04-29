"""
Generic retry decorator for retrying functions on exceptions.
"""

import functools
import logging
import time
from typing import Any, Callable, Type, TypeVar, cast

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 5,
    on_exceptions: tuple[Type[BaseException], ...] | None = None,
    backoff: bool = False,
    max_total_delay: float | None = None,
) -> Callable[[F], F]:
    """
    Decorator to retry a function on exceptions.

    Args:
        max_attempts: Maximum number of attempts before failing.
        delay_seconds: Delay between retries in seconds.
        on_exceptions: Only retry on these exceptions. If None, retry on all.
        backoff: If True, double the delay after each failure.
        max_total_delay: Max cumulative delay time. Abort if exceeded.

    Returns:
        Wrapped function with retry logic.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay_seconds
            total_delay = 0.0

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # If filtering by exception types
                    if on_exceptions is not None and not isinstance(e, on_exceptions):
                        raise

                    logger.warning(f"Attempt {attempt}/{max_attempts} failed in {func.__name__}: {e}")

                    if attempt == max_attempts:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise

                    if max_total_delay is not None and (total_delay + current_delay) > max_total_delay:
                        logger.warning(f"Max total delay {max_total_delay}s exceeded, aborting retries.")
                        raise

                    time.sleep(current_delay)
                    total_delay += current_delay

                    if backoff:
                        current_delay *= 2

            # Should be unreachable, but make pylint happy
            raise RuntimeError(f"Unreachable code reached in retry wrapper for {func.__name__}")

        return cast(F, wrapper)

    return decorator
