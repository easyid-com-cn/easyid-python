"""Billing APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .transport import Transport


@dataclass(frozen=True)
class BillingBalanceResult:
    app_id: str
    available_cents: int


@dataclass(frozen=True)
class BillingRecord:
    id: int
    app_id: str
    request_id: str
    change_cents: int
    balance_before: int
    balance_after: int
    reason: str
    operator: str
    created_at: int


@dataclass(frozen=True)
class BillingRecordsResult:
    total: int
    page: int
    records: List[BillingRecord]


class BillingService:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def balance(self, *, app_id: str) -> BillingBalanceResult:
        data = self._transport.request_json(
            "GET",
            "/v1/billing/balance",
            query={"app_id": app_id},
        )
        return BillingBalanceResult(**data)

    def records(self, *, app_id: str, page: int = 1, page_size: int = 20) -> BillingRecordsResult:
        if page <= 0:
            page = 1
        if page_size <= 0:
            page_size = 20
        else:
            page_size = min(page_size, 100)
        data = self._transport.request_json(
            "GET",
            "/v1/billing/records",
            query={"app_id": app_id, "page": page, "page_size": page_size},
        )
        records = [BillingRecord(**record) for record in data.get("records", [])]
        return BillingRecordsResult(total=data["total"], page=data["page"], records=records)
