class CartError(Exception):
    """Base cart domain error."""


class CartProductNotFoundError(CartError):
    pass


class CartStoreConflictError(CartError):
    pass


class CartItemNotFoundError(CartError):
    pass
