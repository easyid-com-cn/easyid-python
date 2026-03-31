"""Risk APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .transport import Transport


@dataclass(frozen=True)
class RiskDetails:
    rule_score: Optional[int]
    ml_score: Optional[int]


@dataclass(frozen=True)
class RiskScoreResult:
    risk_score: int
    reasons: List[str]
    recommendation: str
    details: RiskDetails


@dataclass(frozen=True)
class StoreFingerprintResult:
    device_id: str
    stored: bool


class RiskService:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def score(
        self,
        *,
        ip: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        device_id: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        user_agent: Optional[str] = None,
        action: Optional[str] = None,
        amount: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskScoreResult:
        body = {
            "ip": ip,
            "device_fingerprint": device_fingerprint,
            "device_id": device_id,
            "phone": phone,
            "email": email,
            "user_agent": user_agent,
            "action": action,
            "amount": amount,
            "context": context,
        }
        data = self._transport.request_json(
            "POST",
            "/v1/risk/score",
            body={key: value for key, value in body.items() if value is not None},
        )
        details = data.get("details", {})
        return RiskScoreResult(
            risk_score=data["risk_score"],
            reasons=list(data.get("reasons", [])),
            recommendation=data["recommendation"],
            details=RiskDetails(
                rule_score=details.get("rule_score"),
                ml_score=details.get("ml_score"),
            ),
        )

    def store_fingerprint(self, *, device_id: str, fingerprint: Dict[str, Any]) -> StoreFingerprintResult:
        data = self._transport.request_json(
            "POST",
            "/v1/device/fingerprint",
            body={"device_id": device_id, "fingerprint": fingerprint},
        )
        return StoreFingerprintResult(**data)

