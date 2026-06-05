"""Excepciones de dominio del módulo products."""


class DomainValidationError(ValueError):
    pass


class InvalidProductPriceError(DomainValidationError):
    pass


class InsufficientStockError(DomainValidationError):
    pass
