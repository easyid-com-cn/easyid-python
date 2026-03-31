"""ID card APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .transport import FileInput, Transport, make_multipart_part


@dataclass(frozen=True)
class IDCardVerifyResult:
    result: bool
    match: bool
    supplier: str
    score: float
    raw: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class IDCardOCRResult:
    side: str
    name: str = ""
    id_number: str = ""
    gender: str = ""
    nation: str = ""
    birth: str = ""
    address: str = ""
    issue: str = ""
    valid: str = ""


class IDCardService:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def verify2(self, *, name: str, id_number: str, trace_id: Optional[str] = None) -> IDCardVerifyResult:
        data = self._transport.request_json(
            "POST",
            "/v1/idcard/verify2",
            body=_compact({"name": name, "id_number": id_number, "trace_id": trace_id}),
        )
        return IDCardVerifyResult(**data)

    def verify3(
        self,
        *,
        name: str,
        id_number: str,
        mobile: str,
        trace_id: Optional[str] = None,
    ) -> IDCardVerifyResult:
        data = self._transport.request_json(
            "POST",
            "/v1/idcard/verify3",
            body=_compact(
                {
                    "name": name,
                    "id_number": id_number,
                    "mobile": mobile,
                    "trace_id": trace_id,
                }
            ),
        )
        return IDCardVerifyResult(**data)

    def ocr(self, *, side: str, image: FileInput, filename: Optional[str] = None) -> IDCardOCRResult:
        data = self._transport.request_multipart(
            "/v1/ocr/idcard",
            fields={"side": side},
            files=[make_multipart_part("image", image, filename)],
        )
        return IDCardOCRResult(**data)


def _compact(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
