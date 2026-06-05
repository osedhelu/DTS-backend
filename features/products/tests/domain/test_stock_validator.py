from decimal import Decimal

import pytest

from features.products.domain.entities import Product, ProductType
from features.products.domain.exceptions import InsufficientStockError
from features.products.domain.services import StockValidator


def test_insufficient_stock_raises():
    product = Product(
        name="Hamburguesa",
        price=Decimal("15000"),
        store_id=1,
        stock=3,
    )

    StockValidator.validate(product, quantity=2)

    with pytest.raises(InsufficientStockError, match="Stock insuficiente"):
        StockValidator.validate(product, quantity=5)

    with pytest.raises(InsufficientStockError, match="cantidad debe ser positiva"):
        StockValidator.validate(product, quantity=0)


def test_service_skips_stock_validation():
    service = Product(
        name="Limpieza profunda",
        price=Decimal("85000"),
        store_id=1,
        product_type=ProductType.SERVICE,
        stock=0,
        duration_minutes=180,
    )

    StockValidator.validate(service, quantity=1)
    StockValidator.validate(service, quantity=100)
