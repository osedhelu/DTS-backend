"""Excepciones de dominio del módulo stores."""


class DomainValidationError(ValueError):
    pass


class InvalidGeoLocationError(DomainValidationError):
    pass


class StoreNotFoundError(DomainValidationError):
    pass


class NotStoreOwnerError(DomainValidationError):
    pass
