import time
import threading


class LeakyBucket(object):  # pylint: disable=too-few-public-methods
    def __init__(self, rate):
        self._rate = rate
        self._lock = threading.Lock()
        self._last_time = int(time.time())
        self._token = 0

    def acquire(self, token, timeout=None):
        delay = 1
        while True:
            with self._lock:  # pylint: disable=not-context-manager
                now = time.time()
                diff = now - self._last_time
                if diff:
                    self._token += self._rate * diff
                    self._last_time = now
                    if token <= self._token:
                        self._token -= token
                        return True

                    if isinstance(timeout, (int, float)):
                        if timeout <= 0:
                            return False
                        timeout -= delay
            time.sleep(delay)
