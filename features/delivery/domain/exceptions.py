"""Excepciones de dominio del módulo delivery."""


class DomainValidationError(ValueError):
    pass


class InvalidTrackingPointError(DomainValidationError):
    pass
