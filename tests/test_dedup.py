import time

from app.pipeline.dedup import Deduplicator


def test_dedup_ttl_behavior():
    d = Deduplicator(ttl_seconds=1)
    assert d.hit('u1', '你好') is False
    assert d.hit('u1', '你好') is True
    time.sleep(1.05)
    assert d.hit('u1', '你好') is False
