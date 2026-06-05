"""Excepciones de dominio del módulo notifications."""


class DomainValidationError(ValueError):
    pass


class PushTemplateNotFoundError(DomainValidationError):
    pass


class FCMClientError(DomainValidationError):
    pass


class FCMNotConfiguredError(FCMClientError):
    pass


class FCMSendError(FCMClientError):
    pass
