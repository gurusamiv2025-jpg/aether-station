import time

from rate_limit import RateLimiter


def test_initial_bucket_allows_burst():
    rl = RateLimiter(bucket_size=5, refill_per_sec=0.0)
    allowed = [rl.check("ip") for _ in range(5)]
    assert all(allowed)


def test_excess_requests_denied():
    rl = RateLimiter(bucket_size=3, refill_per_sec=0.0)
    [rl.check("ip") for _ in range(3)]
    assert not rl.check("ip")


def test_refill_eventually_allows_again():
    rl = RateLimiter(bucket_size=1, refill_per_sec=10.0)
    assert rl.check("ip")
    assert not rl.check("ip")
    time.sleep(0.15)
    assert rl.check("ip")


def test_different_clients_have_independent_buckets():
    rl = RateLimiter(bucket_size=1, refill_per_sec=0.0)
    assert rl.check("ip_a")
    assert rl.check("ip_b")
    assert not rl.check("ip_a")
    assert not rl.check("ip_b")


def test_remaining_reports_initial_size_for_unseen_client():
    rl = RateLimiter(bucket_size=42)
    assert rl.remaining("never_seen") == 42
