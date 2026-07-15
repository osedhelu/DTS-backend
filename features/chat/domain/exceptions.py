"""Excepciones de dominio del módulo chat."""


class DomainValidationError(ValueError):
    pass


class UnauthorizedChatAccessError(DomainValidationError):
    pass


class EmptyChatMessageError(DomainValidationError):
    pass
