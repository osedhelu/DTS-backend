from decimal import Decimal
from unittest.mock import MagicMock

from features.products.application.dto import (
    CreateProductDTO,
    CreateServiceDTO,
    CreateSubcategoryDTO,
    DeactivateProductDTO,
)
from features.products.application.use_cases.manage_category import CreateSubcategoryUseCase
from features.products.application.use_cases.manage_product import (
    CreateProductUseCase,
    CreateServiceUseCase,
    DeactivateProductUseCase,
)
from features.products.domain.entities import Category, Product, ProductType
from features.stores.domain.entities import Store, StoreStatus


def test_create_product():
    product_repository = MagicMock()
    category_repository = MagicMock()
    store_repository = MagicMock()

    store_repository.get_by_id.return_value = Store(
        id=1, name="Restaurante", owner_id=10, status=StoreStatus.OPEN
    )
    category_repository.get_by_id.return_value = Category(
        id=5, name="Comida", store_id=1
    )

    created = Product(
        id=1,
        name="Hamburguesa",
        price=Decimal("15990"),
        store_id=1,
        stock=20,
        category_id=5,
        product_type=ProductType.PHYSICAL,
    )
    product_repository.create.return_value = created

    use_case = CreateProductUseCase(product_repository, category_repository, store_repository)
    result = use_case.execute(
        CreateProductDTO(
            store_id=1,
            owner_id=10,
            name="  Hamburguesa  ",
            price=Decimal("15990"),
            stock=20,
            category_id=5,
        )
    )

    product_repository.create.assert_called_once()
    call_data = product_repository.create.call_args[0][0]
    assert call_data["name"] == "Hamburguesa"
    assert call_data["product_type"] == ProductType.PHYSICAL
    assert call_data["stock"] == 20
    assert result == created


def test_create_service():
    product_repository = MagicMock()
    category_repository = MagicMock()
    store_repository = MagicMock()

    store_repository.get_by_id.return_value = Store(
        id=2, name="Limpieza Express", owner_id=20, status=StoreStatus.OPEN
    )
    category_repository.get_by_id.side_effect = lambda cid: {
        10: Category(id=10, name="Servicios del hogar", store_id=2),
        11: Category(id=11, name="Limpieza", store_id=2, parent_id=10),
    }[cid]

    created = Product(
        id=2,
        name="Limpieza profunda",
        price=Decimal("85000"),
        store_id=2,
        product_type=ProductType.SERVICE,
        category_id=10,
        subcategory_id=11,
        duration_minutes=180,
        requires_on_site_visit=True,
    )
    product_repository.create.return_value = created

    use_case = CreateServiceUseCase(product_repository, category_repository, store_repository)
    result = use_case.execute(
        CreateServiceDTO(
            store_id=2,
            owner_id=20,
            name="Limpieza profunda",
            price=Decimal("85000"),
            category_id=10,
            subcategory_id=11,
            duration_minutes=180,
            description="Incluye cocina y baños",
        )
    )

    call_data = product_repository.create.call_args[0][0]
    assert call_data["product_type"] == ProductType.SERVICE
    assert call_data["stock"] == 0
    assert call_data["duration_minutes"] == 180
    assert call_data["requires_on_site_visit"] is True
    assert result.is_service is True


def test_deactivate_product():
    product_repository = MagicMock()
    store_repository = MagicMock()

    product_repository.get_by_id.return_value = Product(
        id=7,
        name="Hamburguesa",
        price=Decimal("15990"),
        store_id=1,
    )
    store_repository.get_by_id.return_value = Store(
        id=1, name="Restaurante", owner_id=10, status=StoreStatus.OPEN
    )
    deactivated = Product(
        id=7,
        name="Hamburguesa",
        price=Decimal("15990"),
        store_id=1,
        is_active=False,
    )
    product_repository.deactivate.return_value = deactivated

    use_case = DeactivateProductUseCase(product_repository, store_repository)
    result = use_case.execute(DeactivateProductDTO(product_id=7, owner_id=10))

    product_repository.deactivate.assert_called_once_with(7)
    assert result.is_active is False


def test_create_subcategory():
    category_repository = MagicMock()
    store_repository = MagicMock()

    store_repository.get_by_id.return_value = Store(
        id=1, name="Tienda", owner_id=10, status=StoreStatus.OPEN
    )
    category_repository.get_by_id.return_value = Category(
        id=10, name="Servicios del hogar", store_id=1
    )
    created = Category(id=11, name="Limpieza", store_id=1, parent_id=10)
    category_repository.create.return_value = created

    use_case = CreateSubcategoryUseCase(category_repository, store_repository)
    result = use_case.execute(
        CreateSubcategoryDTO(
            store_id=1,
            owner_id=10,
            parent_id=10,
            name="  Limpieza  ",
        )
    )

    category_repository.create.assert_called_once_with(
        {
            "name": "Limpieza",
            "store_id": 1,
            "parent_id": 10,
        }
    )
    assert result.is_subcategory is True
    assert result.parent_id == 10
