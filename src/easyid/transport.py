"""HTTP transport for the EasyID SDK."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, BinaryIO, Dict, Iterable, Mapping, Optional, Tuple, Union
from urllib.parse import urlencode

import requests

from .error import APIError
from .signer import sign

DEFAULT_BASE_URL = "https://api.easyid.com"
MAX_RESPONSE_BYTES = 10 << 20
SDK_VERSION = "1.0.0"

FileInput = Union[bytes, bytearray, BinaryIO]


@dataclass(frozen=True)
class MultipartPart:
    field_name: str
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


class Transport:
    """Low-level HTTP transport shared by all services."""

    def __init__(
        self,
        *,
        key_id: str,
        secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self.key_id = key_id
        self.secret = secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.user_agent = user_agent or f"easyid-python/{SDK_VERSION}"

    def request_json(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        body_bytes = b""
        if body is not None:
            body_bytes = json.dumps(
                body,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        return self._send(
            method=method,
            path=path,
            query=self._normalize_query(query),
            body_bytes=body_bytes,
            content_type="application/json",
        )

    def request_multipart(
        self,
        path: str,
        *,
        fields: Optional[Mapping[str, str]] = None,
        files: Optional[Iterable[MultipartPart]] = None,
    ) -> Any:
        request = requests.Request(
            method="POST",
            url=self.base_url + path,
            data=fields or {},
            files=[
                (
                    part.field_name,
                    (part.filename, part.content, part.content_type),
                )
                for part in (files or [])
            ],
        )
        prepared = self.session.prepare_request(request)
        body = prepared.body
        if body is None:
            body_bytes = b""
        elif isinstance(body, bytes):
            body_bytes = body
        else:
            body_bytes = body.encode("utf-8")
        return self._send(
            method="POST",
            path=path,
            query=None,
            body_bytes=body_bytes,
            content_type=prepared.headers["Content-Type"],
        )

    def _send(
        self,
        *,
        method: str,
        path: str,
        query: Optional[Dict[str, str]],
        body_bytes: bytes,
        content_type: str,
    ) -> Any:
        timestamp = str(int(time.time()))
        signature = sign(self.secret, timestamp, query, body_bytes)

        url = self.base_url + path
        if query:
            url = f"{url}?{urlencode(sorted(query.items()))}"

        request = requests.Request(method=method, url=url, data=body_bytes)
        prepared = self.session.prepare_request(request)
        prepared.headers["Content-Type"] = content_type
        prepared.headers["X-Key-ID"] = self.key_id
        prepared.headers["X-Timestamp"] = timestamp
        prepared.headers["X-Signature"] = signature
        prepared.headers["User-Agent"] = self.user_agent

        response = self.session.send(prepared, timeout=self.timeout, stream=True)
        raw = self._read_response(response)
        if response.status_code < 200 or response.status_code >= 300:
            api_error = self._maybe_api_error(raw)
            if api_error is not None:
                raise api_error
            raise requests.HTTPError(
                f"easyid: http status {response.status_code}",
                response=response,
            )

        try:
            envelope = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"easyid: decode response (status={response.status_code}): {exc}") from exc

        code = int(envelope.get("code", 0))
        if code != 0:
            raise APIError(code, str(envelope.get("message", "")), str(envelope.get("request_id", "")))
        return envelope.get("data")

    def _read_response(self, response: requests.Response) -> bytes:
        chunks = []
        total = 0
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise ValueError("easyid: response exceeds 10 MB limit")
                chunks.append(chunk)
        finally:
            response.close()
        return b"".join(chunks)

    def _maybe_api_error(self, raw: bytes) -> Optional[APIError]:
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        code_value = envelope.get("code", 0)
        if code_value in (None, ""):
            return None
        code = int(code_value)
        if code == 0:
            return None
        return APIError(code, str(envelope.get("message", "")), str(envelope.get("request_id", "")))

    @staticmethod
    def _normalize_query(query: Optional[Mapping[str, Any]]) -> Optional[Dict[str, str]]:
        if not query:
            return None
        return {str(key): str(value) for key, value in query.items()}


def make_multipart_part(field_name: str, file_obj: FileInput, filename: Optional[str]) -> MultipartPart:
    """Create a :class:`MultipartPart` from bytes or a binary file-like object."""

    if isinstance(file_obj, (bytes, bytearray)):
        content = bytes(file_obj)
        resolved_name = filename or "upload.bin"
    else:
        content = file_obj.read()
        if not isinstance(content, bytes):
            raise TypeError("easyid: file object must return bytes")
        guessed_name = getattr(file_obj, "name", None)
        resolved_name = filename or (os.path.basename(guessed_name) if guessed_name else "upload.bin")
    return MultipartPart(field_name=field_name, filename=resolved_name, content=content)
