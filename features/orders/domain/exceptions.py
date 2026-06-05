"""Excepciones de dominio del módulo orders."""


class DomainValidationError(ValueError):
    pass


class InvalidOrderTransitionError(DomainValidationError):
    pass
