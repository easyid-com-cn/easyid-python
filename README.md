# easyid

Official Python SDK for the EasyID API.

## Installation

```bash
pip install easyid
```

## Quick Start

```python
from easyid import EasyID

client = EasyID("ak_3f9a2b1c7d4e8f0a", "sk_test")

result = client.idcard.verify2(
    name="张三",
    id_number="110101199001011234",
)
print(result.result, result.supplier)
```

## Features

- Automatic HMAC-SHA256 request signing
- Grouped services for `idcard`, `phone`, `face`, `bank`, `risk`, and `billing`
- Typed response dataclasses
- `APIError` for service-side business errors
- Configurable base URL, timeout, and custom `requests.Session`

