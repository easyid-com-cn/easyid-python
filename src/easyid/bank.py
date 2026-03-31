"""Bank APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .transport import Transport


@dataclass(frozen=True)
class BankVerify4Result:
    result: bool
    match: bool
    bank_name: str
    supplier: str
    score: float
    masked_bank_card: str
    card_type: str


class BankService:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def verify4(
        self,
        *,
        name: str,
        id_number: str,
        bank_card: str,
        mobile: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> BankVerify4Result:
        body = {
            "name": name,
            "id_number": id_number,
            "bank_card": bank_card,
            "mobile": mobile,
            "trace_id": trace_id,
        }
        data = self._transport.request_json(
            "POST",
            "/v1/bank/verify4",
            body={key: value for key, value in body.items() if value is not None},
        )
        return BankVerify4Result(**data)

