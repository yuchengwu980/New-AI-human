import time

from app.pipeline.ratelimit import RateLimiter


def test_ratelimit_user_and_global():
    r = RateLimiter(user_window_seconds=1, global_window_seconds=1, global_max=2)
    assert r.hit('u1') is False
    assert r.hit('u1') is True

    time.sleep(1.05)
    assert r.hit('u1') is False
    assert r.hit('u2') is False
    assert r.hit('u3') is True
