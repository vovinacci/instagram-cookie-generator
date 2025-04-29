"""
Unit tests for the retry decorator in src.instagram_cookie_generator.retry.
"""

import time

import pytest

from instagram_cookie_generator.retry import retry


def test_retry_success_first_try() -> None:
    """Function succeeds immediately, no retries needed."""

    @retry(max_attempts=3, delay_seconds=0)
    def succeed() -> str:
        return "ok"

    assert succeed() == "ok"


def test_retry_success_after_failures() -> None:
    """Function fails first, then succeeds."""
    call_count = {"count": 0}

    @retry(max_attempts=3, delay_seconds=0)
    def flaky() -> str:
        if call_count["count"] < 2:
            call_count["count"] += 1
            raise ValueError("Temporary failure")
        return "ok"

    assert flaky() == "ok"
    assert call_count["count"] == 2


def test_retry_fail_all_attempts() -> None:
    """Function fails all attempts and raises the final exception."""

    @retry(max_attempts=3, delay_seconds=0)
    def always_fail() -> None:
        raise ValueError("Permanent failure")

    with pytest.raises(ValueError, match="Permanent failure"):
        always_fail()


def test_retry_only_specific_exceptions() -> None:
    """Retry only on certain exceptions, not others."""
    call_count = {"count": 0}

    class RetriableError(Exception):
        pass

    class FatalError(Exception):
        pass

    @retry(max_attempts=3, delay_seconds=0, on_exceptions=(RetriableError,))
    def sometimes_fails() -> str:
        if call_count["count"] == 0:
            call_count["count"] += 1
            raise RetriableError("Retry this")
        if call_count["count"] == 1:
            raise FatalError("Do not retry this")

        return "ok"

    with pytest.raises(FatalError, match="Do not retry this"):
        sometimes_fails()


def test_retry_with_exponential_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test exponential backoff delay is approximately increasing."""

    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(time, "sleep", fake_sleep)

    call_count = {"count": 0}

    @retry(max_attempts=4, delay_seconds=1, backoff=True, jitter=0)
    def flaky() -> str:
        if call_count["count"] < 3:
            call_count["count"] += 1
            raise ValueError("Temporary failure")
        return "ok"

    result = flaky()
    assert result == "ok"

    # Should see delays roughly 1, 2, 4 (doubling each time)
    assert sleep_calls == [1, 2, 4]


def test_retry_respects_max_total_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that retries stop when max_total_delay is exceeded."""

    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(time, "sleep", fake_sleep)

    @retry(max_attempts=10, delay_seconds=2, backoff=True, max_total_delay=5)
    def always_fail() -> None:
        raise ValueError("Failing function")

    with pytest.raises(ValueError):
        always_fail()

    # Should have stopped before exceeding total sleep time
    # Sleep should have happened only twice: 2s and then 4s (cumulative ~6s, but max 5s)
    assert len(sleep_calls) <= 2
