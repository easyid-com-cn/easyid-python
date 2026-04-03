"""Public client entrypoint for the EasyID SDK."""

from __future__ import annotations

import re
from typing import Optional

import requests

from .bank import BankService
from .billing import BillingService
from .face import FaceService
from .idcard import IDCardService
from .phone import PhoneService
from .risk import RiskService
from .transport import DEFAULT_BASE_URL, SDK_VERSION, Transport

_KEY_ID_RE = re.compile(r"^ak_[0-9a-zA-Z_]+$")


class EasyID:
    """EasyID API client.

    The client is safe to reuse across requests.
    """

    version = SDK_VERSION

    def __init__(
        self,
        key_id: str,
        secret: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not _KEY_ID_RE.fullmatch(key_id):
            raise ValueError(f"easyid: key_id must match ak_<hex>, got: {key_id}")
        if not secret:
            raise ValueError("easyid: secret must not be empty")

        self._transport = Transport(
            key_id=key_id,
            secret=secret,
            base_url=base_url,
            timeout=timeout,
            session=session,
        )
        self.idcard = IDCardService(self._transport)
        self.phone = PhoneService(self._transport)
        self.face = FaceService(self._transport)
        self.bank = BankService(self._transport)
        self.risk = RiskService(self._transport)
        self.billing = BillingService(self._transport)

