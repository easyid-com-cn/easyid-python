# EasyID Python SDK

EasyID Python SDK 是易验云身份验证 API 的官方 Python 客户端。

English README: [README.md](README.md)

EasyID 提供身份证核验、手机号核验、人脸识别、银行卡核验、风控评分等能力。本 SDK 适用于服务端应用，自动处理认证头、签名和统一响应解析。

## 安装

```bash
pip install easyid-python
```

如果是开发调试当前仓库，也可以在 `python/` 目录下执行：

```bash
pip install -e .
```

## 快速开始

```python
from easyid import EasyID, APIError

client = EasyID("ak_xxx", "sk_xxx")

try:
    result = client.idcard.verify2(name="张三", id_number="110101199001011234")
    print("是否匹配：", result.match)
except APIError as exc:
    print(exc.code, exc.message, exc.request_id)
```

## 已支持接口

- `client.idcard.verify2()`：身份证二要素核验
- `client.idcard.verify3()`：身份证三要素核验
- `client.idcard.ocr()`：身份证 OCR
- `client.phone.status()`：手机号状态查询
- `client.phone.verify3()`：手机号三要素核验
- `client.face.liveness()`：人脸活体检测
- `client.face.compare()`：人脸比对
- `client.face.verify()`：人脸核验
- `client.bank.verify4()`：银行卡四要素核验
- `client.risk.score()`：风控评分
- `client.risk.store_fingerprint()`：存储设备指纹
- `client.billing.balance()`：查询账户余额
- `client.billing.records()`：查询账单记录

## 配置项

- `base_url`：自定义 API 地址
- `timeout`：请求超时，单位秒
- `session`：自定义 `requests.Session`

## 错误处理

服务端业务错误会抛出 `APIError`。

```python
from easyid import APIError

try:
    client.phone.status(phone="13800138000")
except APIError as exc:
    print(exc.code, exc.message, exc.request_id)
```

## 安全说明

- 这是服务端 SDK，不要在浏览器、移动端或其他不可信环境暴露 `secret`
- `key_id` 必须符合 `ak_[0-9a-f]+`
- SDK 会自动处理 HMAC-SHA256 签名和认证请求头

## 官方资源

- 官网：`https://www.easyid.com.cn/`
- GitHub：`https://github.com/easyid-com-cn/`
