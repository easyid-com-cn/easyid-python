"""Phone APIs."""

from __future__ import annotations

from dataclasses import dataclass

from .transport import Transport


@dataclass(frozen=True)
class PhoneStatusResult:
    status: str
    carrier: str
    province: str
    roaming: bool


@dataclass(frozen=True)
class PhoneVerify3Result:
    result: bool
    match: bool
    supplier: str
    score: float


class PhoneService:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def status(self, *, phone: str) -> PhoneStatusResult:
        data = self._transport.request_json(
            "GET",
            "/v1/phone/status",
            query={"phone": phone},
        )
        return PhoneStatusResult(**data)

    def verify3(self, *, name: str, id_number: str, mobile: str) -> PhoneVerify3Result:
        data = self._transport.request_json(
            "POST",
            "/v1/phone/verify3",
            body={"name": name, "id_number": id_number, "mobile": mobile},
        )
        return PhoneVerify3Result(**data)
