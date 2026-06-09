"""Excepciones de dominio del módulo accounts."""


class DomainValidationError(ValueError):
    """Error de validación en reglas de dominio."""


class InvalidEmailError(DomainValidationError):
    pass


class InvalidPhoneError(DomainValidationError):
    pass


class DuplicateEmailError(DomainValidationError):
    pass


class VerificationTokenExpiredError(DomainValidationError):
    pass


class VerificationTokenAlreadyUsedError(DomainValidationError):
    pass


class VerificationTokenNotFoundError(DomainValidationError):
    pass


class EmailAlreadyVerifiedError(DomainValidationError):
    pass


class InvalidCategoryTemplateError(DomainValidationError):
    pass


class PasswordResetTokenNotFoundError(DomainValidationError):
    pass


class PasswordResetTokenExpiredError(DomainValidationError):
    pass


class PasswordResetTokenAlreadyUsedError(DomainValidationError):
    pass
