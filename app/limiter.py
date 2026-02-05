from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _client_ip(request: Request) -> str:
    # No confiar en X-Forwarded-For por defecto (se puede spoofear).
    trust_xff = os.getenv("TRUST_X_FORWARDED_FOR", "0").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    xff = request.headers.get("x-forwarded-for")
    if trust_xff and xff:
        return xff.split(",", 1)[0].strip()
    return get_remote_address(request)


_DEFAULT_LIMIT = os.getenv("RATE_LIMIT_DEFAULT", "120/minute")
_BURST_LIMIT = os.getenv("RATE_LIMIT_BURST", "10/second")

limiter = Limiter(
    key_func=_client_ip,
    default_limits=[_DEFAULT_LIMIT, _BURST_LIMIT],
    headers_enabled=True,
)
