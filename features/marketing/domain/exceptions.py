"""Excepciones de dominio del módulo marketing."""


class DomainValidationError(ValueError):
    pass


class InvalidCouponError(DomainValidationError):
    pass


class CouponNotApplicableError(DomainValidationError):
    pass
