"""Excepciones de dominio del módulo stores."""


class DomainValidationError(ValueError):
    pass


class InvalidGeoLocationError(DomainValidationError):
    pass
