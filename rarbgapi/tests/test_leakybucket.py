import time

import pytest
from rarbgapi.leakybucket import LeakyBucket


def test_acquire():
    bucket = LeakyBucket(0.5)
    start = time.time()
    assert bucket.acquire(1) is True
    end = time.time()
    assert end-start >= 2.0


def test_acquire_immediate():
    bucket = LeakyBucket(1000)
    start = time.time()
    assert bucket.acquire(1) is True
    end = time.time()
    assert end-start < 0.1


def test_acquire_timeout():
    bucket = LeakyBucket(1)
    assert bucket.acquire(3000, timeout=1) is False
