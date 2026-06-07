from decimal import Decimal

import pytest

from features.products.domain.entities import ProductIngredient, ProductVariant
from features.products.domain.exceptions import (
    InvalidIngredientError,
    InvalidProductPriceError,
    InvalidVariantError,
)


def test_product_variant_price():
    variant = ProductVariant(name="Grande", price=Decimal("18990.00"), sort_order=2)
    assert variant.name == "Grande"
    assert variant.price == Decimal("18990.00")
    assert variant.sort_order == 2


def test_product_variant_rejects_empty_name():
    with pytest.raises(InvalidVariantError, match="nombre"):
        ProductVariant(name="  ", price=Decimal("10000"))


def test_product_variant_rejects_non_positive_price():
    with pytest.raises(InvalidProductPriceError):
        ProductVariant(name="Mediana", price=Decimal("0"))


def test_product_ingredients_validation():
    ingredient = ProductIngredient(name="Queso", is_allergen=True)
    assert ingredient.name == "Queso"
    assert ingredient.is_allergen is True


def test_product_ingredient_rejects_empty_name():
    with pytest.raises(InvalidIngredientError, match="nombre"):
        ProductIngredient(name="")
