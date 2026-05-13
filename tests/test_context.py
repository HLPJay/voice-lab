"""Tests for app.core.context module."""

import pytest

from app.core.context import get_job_id, reset_job_id, set_job_id


def test_job_id_context_set_and_reset():
    """set_job_id returns token, reset_job_id restores previous value."""
    old = get_job_id()
    assert old == ""

    token = set_job_id("job_test_123")
    assert get_job_id() == "job_test_123"

    reset_job_id(token)
    assert get_job_id() == old


def test_job_id_context_nested():
    """Nested set_job_id calls with token reset restores correctly."""
    old = get_job_id()
    assert old == ""

    token1 = set_job_id("job_first")
    assert get_job_id() == "job_first"

    token2 = set_job_id("job_second")
    assert get_job_id() == "job_second"

    # Reset to first
    reset_job_id(token2)
    assert get_job_id() == "job_first"

    # Reset to original
    reset_job_id(token1)
    assert get_job_id() == old


def test_job_id_context_empty_string():
    """Setting empty string clears the context."""
    token = set_job_id("job_abc")
    assert get_job_id() == "job_abc"

    token2 = set_job_id("")
    assert get_job_id() == ""

    reset_job_id(token2)
    assert get_job_id() == "job_abc"

    reset_job_id(token)
    assert get_job_id() == ""