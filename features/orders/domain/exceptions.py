"""Excepciones de dominio del módulo orders."""


class DomainValidationError(ValueError):
    pass


class InvalidOrderTransitionError(DomainValidationError):
    pass


class InvalidOrderItemError(DomainValidationError):
    pass


class EmptyCartError(DomainValidationError):
    pass


class OrderNotFoundError(DomainValidationError):
    pass


class UnauthorizedOrderTransitionError(DomainValidationError):
    pass


class InvalidServiceOrderDetailsError(DomainValidationError):
    pass
