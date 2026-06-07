from features.products.domain.entities import ProductType
from features.products.domain.exceptions import VariantsNotAllowedError
from features.stores.domain.entities import StoreVertical


def assert_variants_allowed(
    *,
    product_type: ProductType,
    store_vertical: StoreVertical,
    has_variants: bool,
) -> None:
    if not has_variants:
        return
    if product_type != ProductType.PHYSICAL:
        raise VariantsNotAllowedError(
            "Las variantes solo aplican a productos físicos"
        )
    if store_vertical == StoreVertical.SERVICES:
        raise VariantsNotAllowedError(
            "Las variantes no están disponibles para comercios de servicios"
        )
