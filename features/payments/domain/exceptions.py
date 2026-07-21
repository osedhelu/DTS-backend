"""Excepciones de dominio — pagos."""


class DomainValidationError(ValueError):
    pass


class PaymentMethodNotFoundError(DomainValidationError):
    pass


class InvalidPaymentTransitionError(DomainValidationError):
    pass
