from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CartItemDTO:
    product_id: int
    quantity: int
    notes: str = ""


@dataclass(frozen=True, slots=True)
class UpsertCartItemDTO:
    customer_id: int
    product_id: int
    quantity: int
    notes: str = ""
    replace_store: bool = True


@dataclass(frozen=True, slots=True)
class UpdateCartItemQuantityDTO:
    customer_id: int
    product_id: int
    quantity: int
