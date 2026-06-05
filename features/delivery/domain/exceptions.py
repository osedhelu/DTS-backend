"""Excepciones de dominio del módulo delivery."""


class DomainValidationError(ValueError):
    pass


class InvalidTrackingPointError(DomainValidationError):
    pass


class UnauthorizedDriverError(DomainValidationError):
    pass


class InvalidOrderStatusForTrackingError(DomainValidationError):
    pass


class ServiceOrderNotTrackableError(DomainValidationError):
    pass


class UnauthorizedTrackingAccessError(DomainValidationError):
    pass
