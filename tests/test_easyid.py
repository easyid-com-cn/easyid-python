from __future__ import annotations

import json
import threading
import unittest

import requests
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

from easyid import APIError, EasyID, is_api_error
from easyid.signer import sign


@dataclass
class RecordedRequest:
    method: str
    path: str
    query: Dict[str, str]
    headers: Dict[str, str]
    body: bytes


class MockHTTPServer:
    def __init__(self, handler: Callable[[RecordedRequest], tuple[int, str, str]]) -> None:
        self._handler = handler
        self.requests: List[RecordedRequest] = []
        self._exc: Optional[Exception] = None
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "MockHTTPServer":
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:
                self._handle()

            def do_POST(self) -> None:
                self._handle()

            def log_message(self, format: str, *args: object) -> None:
                return

            def _handle(self) -> None:
                parsed = urlparse(self.path)
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                request = RecordedRequest(
                    method=self.command,
                    path=parsed.path,
                    query=query,
                    headers={key: value for key, value in self.headers.items()},
                    body=body,
                )
                outer.requests.append(request)
                try:
                    status, content_type, payload = outer._handler(request)
                except Exception as exc:
                    outer._exc = exc
                    body = str(exc).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                body = payload.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        assert self._server is not None
        self._server.shutdown()
        self._server.server_close()
        assert self._thread is not None
        self._thread.join(timeout=5)
        if self._exc is not None and exc_type is None:
            raise self._exc

    @property
    def base_url(self) -> str:
        assert self._server is not None
        host, port = self._server.server_address
        return f"http://{host}:{port}"


class EasyIDTests(unittest.TestCase):
    key_id = "ak_3f9a2b1c7d4e8f0a"
    secret = "sk_test"

    def client(self, server) -> EasyID:
        # Disable system proxy so mock server on 127.0.0.1 is reachable directly.
        session = requests.Session()
        session.trust_env = False
        return EasyID(self.key_id, self.secret, base_url=server.base_url, timeout=5.0, session=session)

    def test_verify2(self) -> None:
        def handler(request: RecordedRequest) -> tuple[int, str, str]:
            self.assertEqual(request.path, "/v1/idcard/verify2")
            self.assertEqual(request.method, "POST")
            self._assert_common_headers(request.headers)
            return 200, "application/json", self._ok({"result": True, "match": True, "supplier": "aliyun", "score": 0.98})

        with MockHTTPServer(handler) as server:
            result = self.client(server).idcard.verify2(name="张三", id_number="110101199001011234")
            self.assertTrue(result.result)
            self.assertEqual(result.supplier, "aliyun")

    def test_verify3(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"result": True, "match": True, "supplier": "tencent", "score": 0.95}))) as server:
            result = self.client(server).idcard.verify3(
                name="张三",
                id_number="110101199001011234",
                mobile="13800138000",
            )
            self.assertTrue(result.match)

    def test_ocr_multipart_signature(self) -> None:
        def handler(request: RecordedRequest) -> tuple[int, str, str]:
            self.assertEqual(request.path, "/v1/ocr/idcard")
            self.assertEqual(request.method, "POST")
            self._assert_common_headers(request.headers)
            expected = sign(self.secret, request.headers["X-Timestamp"], {}, request.body)
            self.assertEqual(request.headers["X-Signature"], expected)
            self.assertIn(b'name="side"', request.body)
            self.assertIn(b'name="image"', request.body)
            return 200, "application/json", self._ok({"side": "front", "name": "张三", "id_number": "110101199001011234"})

        with MockHTTPServer(handler) as server:
            result = self.client(server).idcard.ocr(side="front", image=b"fake-image", filename="id.jpg")
            self.assertEqual(result.name, "张三")

    def test_phone_status_includes_query_in_signature(self) -> None:
        def handler(request: RecordedRequest) -> tuple[int, str, str]:
            self.assertEqual(request.path, "/v1/phone/status")
            self.assertEqual(request.query["phone"], "13800138000")
            self._assert_common_headers(request.headers)
            expected = sign(self.secret, request.headers["X-Timestamp"], request.query, b"")
            self.assertEqual(request.headers["X-Signature"], expected)
            self.assertLessEqual(len(request.headers["X-Timestamp"]), 10)
            return 200, "application/json", self._ok(
                {"status": "real", "carrier": "移动", "province": "广东", "roaming": False}
            )

        with MockHTTPServer(handler) as server:
            result = self.client(server).phone.status(phone="13800138000")
            self.assertEqual(result.status, "real")

    def test_phone_verify3(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"result": True, "match": True, "supplier": "aliyun", "score": 0.99}))) as server:
            result = self.client(server).phone.verify3(
                name="张三",
                id_number="110101199001011234",
                mobile="13800138000",
            )
            self.assertTrue(result.result)

    def test_face_liveness(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"liveness": True, "score": 0.97, "method": "passive", "frames_analyzed": 10, "attack_type": None}))) as server:
            result = self.client(server).face.liveness(media=b"video", mode="passive", filename="video.mp4")
            self.assertTrue(result.liveness)

    def test_face_compare(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"match": True, "score": 0.92}))) as server:
            result = self.client(server).face.compare(image1=b"img1", image2=b"img2", filename1="a.jpg", filename2="b.jpg")
            self.assertTrue(result.match)

    def test_face_verify(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"result": True, "supplier": "aliyun", "score": 0.96}))) as server:
            result = self.client(server).face.verify(id_number="110101199001011234", media_key="oss://bucket/key")
            self.assertTrue(result.result)

    def test_bank_verify4(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"result": True, "match": True, "bank_name": "工商银行", "supplier": "aliyun", "score": 0.99, "masked_bank_card": "6222****1234", "card_type": "debit"}))) as server:
            result = self.client(server).bank.verify4(
                name="张三",
                id_number="110101199001011234",
                bank_card="6222021234567890",
                mobile="13800138000",
            )
            self.assertEqual(result.card_type, "debit")

    def test_risk_score(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"risk_score": 30, "reasons": ["new_device"], "recommendation": "allow", "details": {"rule_score": None, "ml_score": None}}))) as server:
            result = self.client(server).risk.score(ip="1.2.3.4", device_id="dev_abc", action="login")
            self.assertEqual(result.risk_score, 30)
            self.assertEqual(result.details.ml_score, None)

    def test_store_fingerprint(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"device_id": "dev_abc", "stored": True}))) as server:
            result = self.client(server).risk.store_fingerprint(
                device_id="dev_abc",
                fingerprint={"canvas": "hash123", "webgl": "hash456"},
            )
            self.assertTrue(result.stored)

    def test_billing_balance(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", self._ok({"app_id": "app_001", "available_cents": 100000}))) as server:
            result = self.client(server).billing.balance(app_id="app_001")
            self.assertEqual(result.available_cents, 100000)

    def test_billing_records(self) -> None:
        payload = {
            "total": 1,
            "page": 1,
            "records": [
                {
                    "id": 1,
                    "app_id": "app_001",
                    "request_id": "req_001",
                    "change_cents": -100,
                    "balance_before": 100100,
                    "balance_after": 100000,
                    "reason": "idcard_verify2",
                    "operator": "system",
                    "created_at": 1711900000,
                }
            ],
        }
        with MockHTTPServer(lambda request: (200, "application/json", self._ok(payload))) as server:
            result = self.client(server).billing.records(app_id="app_001", page=1, page_size=20)
            self.assertEqual(result.total, 1)
            self.assertEqual(result.records[0].change_cents, -100)

    def test_api_error(self) -> None:
        with MockHTTPServer(lambda request: (200, "application/json", json.dumps({"code": 1001, "message": "invalid key_id", "request_id": "err-rid", "data": None}))) as server:
            with self.assertRaises(APIError) as ctx:
                self.client(server).phone.status(phone="13800138000")
            self.assertTrue(is_api_error(ctx.exception))
            self.assertEqual(ctx.exception.code, 1001)
            self.assertEqual(ctx.exception.request_id, "err-rid")

    def test_http_5xx_non_json(self) -> None:
        with MockHTTPServer(lambda request: (503, "text/html", "<html>503 Service Unavailable</html>")) as server:
            with self.assertRaises(Exception) as ctx:
                self.client(server).phone.status(phone="13800138000")
            self.assertFalse(is_api_error(ctx.exception))

    def test_http_5xx_json_body(self) -> None:
        payload = json.dumps({"code": 5000, "message": "internal server error", "request_id": "err-500", "data": None})
        with MockHTTPServer(lambda request: (500, "application/json", payload)) as server:
            with self.assertRaises(APIError) as ctx:
                self.client(server).phone.status(phone="13800138000")
            self.assertEqual(ctx.exception.code, 5000)

    def test_invalid_key_id(self) -> None:
        for value in ["", "sk_abc", "ak_\r\nEvil: 1", "ak_ space", "ak_has/slash"]:
            with self.assertRaises(ValueError):
                EasyID(value, "sk_secret")

    def test_empty_secret(self) -> None:
        with self.assertRaises(ValueError):
            EasyID(self.key_id, "")

    def test_user_agent_header(self) -> None:
        def handler(request: RecordedRequest) -> tuple[int, str, str]:
            self.assertTrue(request.headers["User-Agent"].startswith("easyid-python/"))
            return 200, "application/json", self._ok(
                {"status": "real", "carrier": "移动", "province": "广东", "roaming": False}
            )

        with MockHTTPServer(handler) as server:
            self.client(server).phone.status(phone="13800138000")

    def _assert_common_headers(self, headers: Dict[str, str]) -> None:
        self.assertEqual(headers["X-Key-ID"], self.key_id)
        self.assertTrue(headers["X-Timestamp"].isdigit())
        self.assertTrue(headers["X-Signature"])

    @staticmethod
    def _ok(data: object) -> str:
        return json.dumps({"code": 0, "message": "success", "request_id": "test-rid", "data": data}, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
