"""Excepciones de dominio del módulo accounts."""


class DomainValidationError(ValueError):
    """Error de validación en reglas de dominio."""


class InvalidEmailError(DomainValidationError):
    pass


class InvalidPhoneError(DomainValidationError):
    pass


class DuplicateEmailError(DomainValidationError):
    pass
