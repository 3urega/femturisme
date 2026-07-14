"""Unit tests for in-memory rate limiting."""
from __future__ import annotations

from app.services.rate_limit import check_and_consume, reset


def _cfg(*, per_ip=3, per_session=3, window=60):
    return {
        'RATE_LIMIT_PER_IP': per_ip,
        'RATE_LIMIT_PER_SESSION': per_session,
        'RATE_LIMIT_WINDOW_SECONDS': window,
    }


def setup_function():
    reset()


def test_allows_up_to_ip_limit():
    cfg = _cfg(per_ip=3, per_session=99)
    assert check_and_consume('1.2.3.4', 'sess-a', cfg) is True
    assert check_and_consume('1.2.3.4', 'sess-a', cfg) is True
    assert check_and_consume('1.2.3.4', 'sess-a', cfg) is True
    assert check_and_consume('1.2.3.4', 'sess-a', cfg) is False


def test_session_limit_independent_of_ip():
    cfg = _cfg(per_ip=99, per_session=2)
    assert check_and_consume('1.1.1.1', 'sess-1', cfg) is True
    assert check_and_consume('2.2.2.2', 'sess-1', cfg) is True
    assert check_and_consume('3.3.3.3', 'sess-1', cfg) is False


def test_different_ips_have_separate_buckets():
    cfg = _cfg(per_ip=1, per_session=99)
    assert check_and_consume('10.0.0.1', 's1', cfg) is True
    assert check_and_consume('10.0.0.1', 's2', cfg) is False
    assert check_and_consume('10.0.0.2', 's1', cfg) is True


def test_zero_limit_disables_bucket():
    cfg = _cfg(per_ip=0, per_session=0)
    for _ in range(5):
        assert check_and_consume('9.9.9.9', 'sess-z', cfg) is True


def test_reset_clears_counters():
    cfg = _cfg(per_ip=1, per_session=1)
    assert check_and_consume('1.0.0.1', 'sess-r', cfg) is True
    assert check_and_consume('1.0.0.1', 'sess-r', cfg) is False
    reset()
    assert check_and_consume('1.0.0.1', 'sess-r', cfg) is True
