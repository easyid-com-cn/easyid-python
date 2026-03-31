# EasyID Python SDK

Official Python SDK for the EasyID identity verification API.

## Install

```bash
pip install easyid
```

## Quick Start

```python
from easyid import EasyID

client = EasyID("ak_xxx", "sk_xxx")
result = client.idcard.verify2(name="张三", id_number="110101199001011234")

print(result.match)
```

## Supported APIs

- IDCard: `verify2`, `verify3`, `ocr`
- Phone: `status`, `verify3`
- Face: `liveness`, `compare`, `verify`
- Bank: `verify4`
- Risk: `score`, `store_fingerprint`
- Billing: `balance`, `records`

## Configuration

- `base_url`
- `timeout`
- `session`

## Error Handling

Service-side business errors raise `APIError`.

```python
from easyid import APIError

try:
    client.phone.status(phone="13800138000")
except APIError as exc:
    print(exc.code, exc.message, exc.request_id)
```

## Security Notice

This is a server-side SDK. Never expose `secret` in browsers, mobile apps, or other untrusted clients.

## More Docs

- [Integration Guide](/Users/nbt-mingyi/mingyi.wu/easyid/sdk/docs/integration-guide.md)
- [Publishing Strategy](/Users/nbt-mingyi/mingyi.wu/easyid/sdk/docs/repository-publishing-strategy.md)
