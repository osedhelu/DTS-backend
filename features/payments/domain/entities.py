"""Entidades de dominio — pagos."""

from enum import StrEnum


class PaymentMethodType(StrEnum):
    QR = "qr"
    CASH = "cash"
    TRANSFER = "transfer"
    INSTRUCTIONS = "instructions"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CASH_ON_DELIVERY = "cash_on_delivery"
