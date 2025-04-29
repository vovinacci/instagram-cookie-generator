"""
Generic retry decorator for retrying functions on exceptions.
Supports:
- Specific exception filtering
- Exponential backoff
- Cumulative delay limit
- Detailed structured logging
"""

import functools
import logging
import random
import time
from typing import Any, Callable, Type, TypeVar, cast

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(  # pylint: disable=too-many-positional-arguments
    max_attempts: int = 3,
    delay_seconds: float = 5,
    on_exceptions: tuple[Type[BaseException], ...] | None = None,
    backoff: bool = False,
    max_total_delay: float | None = None,
    jitter: float = 0.5,
) -> Callable[[F], F]:
    """
    Decorator to retry a function on exceptions.

    Args:
        max_attempts: Maximum number of attempts before failing.
        delay_seconds: Base delay between retries in seconds.
        on_exceptions: Only retry on these exceptions. If None, retry on all.
        backoff: If True, double the delay after each failure.
        max_total_delay: Max cumulative delay time (in seconds). Abort if exceeded.
        jitter: Maximum random jitter to add to each sleep (in seconds).

    Returns:
        Wrapped function with retry logic.

    Example usage:

    ```python
    from instagram_cookie_generator.retry import retry

    @retry(max_attempts=5, delay_seconds=2, backoff=True, jitter=1.0)
    def fragile_task():
        if random.random() < 0.7:
            raise RuntimeError("Transient failure")
        return "Success!"
    ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay_seconds
            total_delay = 0.0
            start_time = time.monotonic()

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    if on_exceptions is not None and not isinstance(e, on_exceptions):
                        raise

                    elapsed = time.monotonic() - start_time
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed in {func.__name__}: {e}. "
                        f"Elapsed {elapsed:.1f}s, total delay {total_delay:.1f}s."
                    )

                    if attempt == max_attempts:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise

                    if max_total_delay is not None and (total_delay + current_delay) > max_total_delay:
                        logger.warning(f"Max total delay {max_total_delay}s exceeded, aborting retries.")
                        raise

                    sleep_time = current_delay + random.uniform(0, jitter)
                    logger.info(f"Sleeping {sleep_time:.2f}s before next retry...")
                    time.sleep(sleep_time)
                    total_delay += sleep_time

                    if backoff:
                        current_delay *= 2

            # Should be unreachable, but we want to make pylint happy
            raise RuntimeError(f"Unreachable code reached in retry wrapper for {func.__name__}")

        return cast(F, wrapper)

    return decorator
