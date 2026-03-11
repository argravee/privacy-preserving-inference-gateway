from collections import defaultdict, deque
from threading import Lock
from time import time

from fastapi import HTTPException, status

_WINDOW_SECONDS = 60
_LIMIT = 20

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def reset_rate_limits() -> None:
    with _lock:
        _hits.clear()


def enforce_infer_rate_limit(tenant_id: str) -> None:
    now = time()
    cutoff = now - _WINDOW_SECONDS

    with _lock:
        bucket = _hits[tenant_id]

        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= _LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Tenant rate limit exceeded",
            )

        bucket.append(now)