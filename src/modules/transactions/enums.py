from enum import Enum


class RawTransactionStatus(str, Enum):
    CREATED = "CREATED"
    BROADCASTED = "BROADCASTED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    DROPPED_AND_REPLACED = "DROPPED_AND_REPLACED"


class TransactionStatus(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


RAW_SYSTEM_TX_STATUS_MAPPING = {
    RawTransactionStatus.CREATED: TransactionStatus.CREATED,
    RawTransactionStatus.BROADCASTED: TransactionStatus.PENDING,
    RawTransactionStatus.PENDING: TransactionStatus.PENDING,
    RawTransactionStatus.CONFIRMED: TransactionStatus.CONFIRMED,
    RawTransactionStatus.FAILED: TransactionStatus.FAILED,
}


class TransactionDirection(str, Enum):
    IN = "IN"
    OUT = "OUT"


class GasPolicy(str, Enum):
    STANDARD = "STANDARD"
    FAST = "FAST"
    FASTEST = "FASTEST"
