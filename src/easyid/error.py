"""Error types for the EasyID SDK."""

from __future__ import annotations


class APIError(Exception):
    """Business error returned by the EasyID API."""

    def __init__(self, code: int, message: str, request_id: str) -> None:
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(f"easyid: code={code} message={message} request_id={request_id}")


def is_api_error(exc: BaseException) -> bool:
    """Return True when *exc* is an :class:`APIError`."""

    return isinstance(exc, APIError)

