import threading

import pytest

from automation.cancellation import CancellationContext, CancellationToken


def test_token_starts_not_cancelled():
    token = CancellationToken()

    assert token.is_cancelled() is False
    assert token.reason == ""


def test_cancel_sets_state_and_reason():
    token = CancellationToken()

    token.cancel("User requested stop.")

    assert token.is_cancelled() is True
    assert token.reason == "User requested stop."


def test_cancel_uses_default_reason_for_empty_reason():
    token = CancellationToken()

    token.cancel("")

    assert token.is_cancelled() is True
    assert token.reason == "Task interrupted by user."


def test_raise_if_cancelled_raises_interrupted_error():
    token = CancellationToken()
    token.cancel("Stop now.")

    with pytest.raises(InterruptedError, match="Stop now."):
        token.raise_if_cancelled()


def test_reset_clears_cancelled_state_and_reason():
    token = CancellationToken()
    token.cancel("Stop now.")

    token.reset()

    assert token.is_cancelled() is False
    assert token.reason == ""
    token.raise_if_cancelled()


def test_context_wraps_a_shared_token():
    token = CancellationToken()
    context = CancellationContext(token)

    context.cancel("Context cancellation.")

    assert context.is_cancelled() is True
    assert token.is_cancelled() is True
    assert token.reason == "Context cancellation."


def test_cancellation_is_visible_across_threads():
    token = CancellationToken()
    observed = threading.Event()

    def wait_for_cancel():
        token.event.wait(timeout=2)
        if token.is_cancelled():
            observed.set()

    worker = threading.Thread(target=wait_for_cancel)
    worker.start()
    token.cancel("Thread-safe stop.")
    worker.join(timeout=3)

    assert not worker.is_alive()
    assert observed.is_set()
