from decimal import Decimal

import pytest

from features.products.domain.entities import Category, Product, ProductType
from features.products.domain.exceptions import InvalidProductPriceError


def test_product_price_positive():
    product = Product(
        name="Hamburguesa clásica",
        price=Decimal("15990.00"),
        store_id=1,
        stock=10,
        category_id=1,
        subcategory_id=2,
        description="Carne 150g, queso, lechuga",
    )

    assert product.price == Decimal("15990.00")
    assert product.product_type == ProductType.PHYSICAL
    assert product.tracks_stock is True
    assert product.requires_on_site_visit is False

    with pytest.raises(InvalidProductPriceError):
        Product(name="Precio cero", price=Decimal("0"), store_id=1)

    with pytest.raises(InvalidProductPriceError):
        Product(name="Precio negativo", price=Decimal("-1"), store_id=1)


def test_category_hierarchy():
    root = Category(name="Servicios del hogar", store_id=1, id=10)
    sub = Category(name="Limpieza", store_id=1, parent_id=10, id=11)

    assert root.is_root is True
    assert root.is_subcategory is False
    assert sub.is_subcategory is True
    assert sub.parent_id == 10


def test_service_product_on_site_visit():
    service = Product(
        name="Limpieza profunda apartamento",
        price=Decimal("85000.00"),
        store_id=1,
        product_type=ProductType.SERVICE,
        category_id=10,
        subcategory_id=11,
        description="Incluye cocina, baños y áreas comunes",
        duration_minutes=180,
    )

    assert service.is_service is True
    assert service.tracks_stock is False
    assert service.requires_on_site_visit is True
    assert service.duration_minutes == 180
    assert service.stock == 0
