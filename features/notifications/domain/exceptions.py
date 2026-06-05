"""Excepciones de dominio del módulo notifications."""


class DomainValidationError(ValueError):
    pass


class PushTemplateNotFoundError(DomainValidationError):
    pass
