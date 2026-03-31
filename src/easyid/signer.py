"""Signing helpers for the EasyID SDK."""

from __future__ import annotations

import hashlib
import hmac
from typing import Mapping, Optional


def sign(secret: str, timestamp: str, query: Optional[Mapping[str, str]], body: bytes) -> str:
    """Return the lowercase hex HMAC-SHA256 signature for a request."""

    parts = []
    if query:
        for key in sorted(query):
            parts.append(f"{key}={query[key]}")
    payload = "&".join(parts)
    if body:
        body_text = body.decode("utf-8")
        payload = f"{payload}&{body_text}" if payload else body_text
    to_sign = f"{timestamp}\n{payload}"
    digest = hmac.new(secret.encode("utf-8"), to_sign.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()

