"""Excepciones de dominio del módulo products."""


class DomainValidationError(ValueError):
    pass


class InvalidProductPriceError(DomainValidationError):
    pass


class InsufficientStockError(DomainValidationError):
    pass


class ProductNotFoundError(DomainValidationError):
    pass


class ProductImageNotFoundError(DomainValidationError):
    pass


class CategoryNotFoundError(DomainValidationError):
    pass


class InvalidCategoryHierarchyError(DomainValidationError):
    pass


class CategoryInUseError(DomainValidationError):
    pass


class VariantsNotAllowedError(DomainValidationError):
    pass


class InvalidVariantError(DomainValidationError):
    pass


class InvalidIngredientError(DomainValidationError):
    pass


class InvalidDynamicFieldError(DomainValidationError):
    pass
