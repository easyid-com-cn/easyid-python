"""Face APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .transport import FileInput, Transport, make_multipart_part


@dataclass(frozen=True)
class LivenessResult:
    liveness: bool
    score: float
    method: str
    frames_analyzed: int
    attack_type: Optional[str]


@dataclass(frozen=True)
class CompareResult:
    match: bool
    score: float


@dataclass(frozen=True)
class FaceVerifyResult:
    result: bool
    supplier: str
    score: float


class FaceService:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def liveness(
        self,
        *,
        media: FileInput,
        mode: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> LivenessResult:
        fields = {}
        if mode is not None:
            fields["mode"] = mode
        data = self._transport.request_multipart(
            "/v1/face/liveness",
            fields=fields,
            files=[make_multipart_part("media", media, filename)],
        )
        return LivenessResult(**data)

    def compare(
        self,
        *,
        image1: FileInput,
        image2: FileInput,
        filename1: Optional[str] = None,
        filename2: Optional[str] = None,
    ) -> CompareResult:
        data = self._transport.request_multipart(
            "/v1/face/compare",
            files=[
                make_multipart_part("image1", image1, filename1),
                make_multipart_part("image2", image2, filename2),
            ],
        )
        return CompareResult(**data)

    def verify(
        self,
        *,
        id_number: str,
        media_key: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> FaceVerifyResult:
        body = {"id_number": id_number}
        if media_key is not None:
            body["media_key"] = media_key
        if callback_url is not None:
            body["callback_url"] = callback_url
        data = self._transport.request_json("POST", "/v1/face/verify", body=body)
        return FaceVerifyResult(**data)

