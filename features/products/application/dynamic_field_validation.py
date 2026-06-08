from features.products.domain.dynamic_fields import (
    resolve_field_config,
    validate_dynamic_values,
    validate_field_config,
)
from features.products.domain.exceptions import CategoryNotFoundError
from features.products.domain.repositories import CategoryRepository


def resolve_product_field_config(
    category_repository: CategoryRepository,
    *,
    store_id: int,
    category_id: int | None,
    subcategory_id: int | None,
) -> dict[str, list[str] | str]:
    category_config: dict[str, list[str] | str] = {}
    subcategory_config: dict[str, list[str] | str] = {}

    if category_id is not None:
        category = category_repository.get_by_id(category_id)
        if category is None or category.store_id != store_id:
            raise CategoryNotFoundError(f"Categoría {category_id} no encontrada")
        category_config = category.field_config or {}

    if subcategory_id is not None:
        subcategory = category_repository.get_by_id(subcategory_id)
        if subcategory is None or subcategory.store_id != store_id:
            raise CategoryNotFoundError(f"Subcategoría {subcategory_id} no encontrada")
        subcategory_config = subcategory.field_config or {}

    return resolve_field_config(category_config, subcategory_config)


def validate_product_dynamic_values(
    category_repository: CategoryRepository,
    *,
    store_id: int,
    category_id: int | None,
    subcategory_id: int | None,
    raw_values,
) -> dict[str, str | list[str]]:
    field_config = resolve_product_field_config(
        category_repository,
        store_id=store_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
    )
    return validate_dynamic_values(field_config, raw_values)


__all__ = [
    "resolve_product_field_config",
    "validate_field_config",
    "validate_product_dynamic_values",
]
