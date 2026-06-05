"""Excepciones de dominio del módulo analytics."""


class DomainValidationError(ValueError):
    pass


class InvalidDailyReportError(DomainValidationError):
    pass
