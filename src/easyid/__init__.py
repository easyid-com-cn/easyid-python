"""EasyID Python SDK."""

from .bank import BankService, BankVerify4Result
from .billing import BillingRecord, BillingRecordsResult, BillingService, BillingBalanceResult
from .client import EasyID
from .error import APIError, is_api_error
from .face import CompareResult, FaceService, FaceVerifyResult, LivenessResult
from .idcard import IDCardOCRResult, IDCardService, IDCardVerifyResult
from .phone import PhoneService, PhoneStatusResult, PhoneVerify3Result
from .risk import RiskDetails, RiskScoreResult, RiskService, StoreFingerprintResult

__version__ = EasyID.version

__all__ = [
    "APIError",
    "BankService",
    "BankVerify4Result",
    "BillingBalanceResult",
    "BillingRecord",
    "BillingRecordsResult",
    "BillingService",
    "CompareResult",
    "EasyID",
    "FaceService",
    "FaceVerifyResult",
    "IDCardOCRResult",
    "IDCardService",
    "IDCardVerifyResult",
    "LivenessResult",
    "PhoneService",
    "PhoneStatusResult",
    "PhoneVerify3Result",
    "RiskDetails",
    "RiskScoreResult",
    "RiskService",
    "StoreFingerprintResult",
    "__version__",
    "is_api_error",
]
