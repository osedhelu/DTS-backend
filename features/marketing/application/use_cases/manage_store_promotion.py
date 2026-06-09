from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from features.marketing.domain.entities import DiscountType, StorePromotion
from features.marketing.domain.exceptions import (
    InvalidStorePromotionError,
    StorePromotionNotFoundError,
)
from features.products.domain.exceptions import ProductNotFoundError
from features.products.domain.dynamic_fields import extract_multi_options
from features.products.infrastructure.models import ProductVariant
from features.products.infrastructure.repositories import DjangoProductRepository
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.infrastructure.repositories import DjangoStoreRepository


class _UnsetType:
    """Marca campos omitidos en PATCH parcial."""


UNSET = _UnsetType()


@dataclass(frozen=True)
class CreateStorePromotionDTO:
    store_id: int
    owner_id: int
    name: str
    discount_type: DiscountType
    discount_value: Decimal
    product_id: int | None = None
    variant_id: int | None = None
    param_key: str | None = None
    param_value: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


@dataclass(frozen=True)
class UpdateStorePromotionDTO:
    promotion_id: int
    store_id: int
    owner_id: int
    name: str | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None
    product_id: int | None = None
    variant_id: int | None = None
    param_key: str | None = None
    param_value: str | None = None
    valid_from: datetime | None | _UnsetType = UNSET
    valid_until: datetime | None | _UnsetType = UNSET
    is_active: bool | None = None


@dataclass(frozen=True)
class DeactivateStorePromotionDTO:
    promotion_id: int
    store_id: int
    owner_id: int


class _StorePromotionOwnershipMixin:
    def _ensure_store_owner(self, store_id: int, owner_id: int) -> None:
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este comercio")

    def _validate_product(self, store_id: int, product_id: int | None) -> None:
        if product_id is None:
            return
        product = self._product_repository.get_by_id(product_id)
        if product is None or product.store_id != store_id:
            raise ProductNotFoundError(f"Producto {product_id} no encontrado")

    def _resolve_product_and_variant(
        self,
        store_id: int,
        product_id: int | None,
        variant_id: int | None,
    ) -> tuple[int | None, int | None]:
        if variant_id is None:
            return product_id, None

        try:
            variant = ProductVariant.objects.select_related("product").get(pk=variant_id)
        except ProductVariant.DoesNotExist as exc:
            raise ProductNotFoundError(f"Variante {variant_id} no encontrada") from exc

        if variant.product.store_id != store_id:
            raise ProductNotFoundError(f"Variante {variant_id} no encontrada")

        resolved_product_id = product_id or variant.product_id
        if resolved_product_id != variant.product_id:
            raise InvalidStorePromotionError(
                "La variante no pertenece al producto seleccionado"
            )

        return resolved_product_id, variant_id

    def _validate_product_param(
        self,
        product_id: int | None,
        param_key: str | None,
        param_value: str | None,
    ) -> tuple[str | None, str | None]:
        if param_key is None and param_value is None:
            return None, None

        if not product_id:
            raise InvalidStorePromotionError("param_key requiere un product_id asociado")

        product = self._product_repository.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(f"Producto {product_id} no encontrado")

        if not param_key or not param_value:
            raise InvalidStorePromotionError("param_key y param_value deben enviarse juntos")

        dynamic_values = product.dynamic_values or {}
        if param_key not in dynamic_values:
            raise InvalidStorePromotionError(
                f"El producto no tiene el parámetro '{param_key}'"
            )

        selected = extract_multi_options(dynamic_values[param_key])
        if param_value not in selected:
            raise InvalidStorePromotionError(
                f"El producto no ofrece '{param_key}' = '{param_value}'"
            )

        return param_key.strip(), param_value.strip()


class CreateStorePromotionUseCase(_StorePromotionOwnershipMixin):
    def __init__(
        self,
        promotion_repository,
        store_repository: DjangoStoreRepository,
        product_repository: DjangoProductRepository,
    ) -> None:
        self._promotion_repository = promotion_repository
        self._store_repository = store_repository
        self._product_repository = product_repository

    def execute(self, dto: CreateStorePromotionDTO) -> StorePromotion:
        self._ensure_store_owner(dto.store_id, dto.owner_id)
        product_id, variant_id = self._resolve_product_and_variant(
            dto.store_id,
            dto.product_id,
            dto.variant_id if not dto.param_key else None,
        )
        param_key, param_value = self._validate_product_param(
            product_id,
            dto.param_key,
            dto.param_value,
        )
        if param_key:
            variant_id = None
        self._validate_product(dto.store_id, product_id)

        promotion = StorePromotion(
            store_id=dto.store_id,
            name=dto.name.strip(),
            discount_type=dto.discount_type,
            discount_value=dto.discount_value,
            product_id=product_id,
            variant_id=variant_id,
            param_key=param_key,
            param_value=param_value,
            valid_from=dto.valid_from,
            valid_until=dto.valid_until,
        )

        return self._promotion_repository.create(
            {
                "store_id": promotion.store_id,
                "name": promotion.name,
                "discount_type": promotion.discount_type.value,
                "discount_value": promotion.discount_value,
                "product_id": promotion.product_id,
                "variant_id": promotion.variant_id,
                "param_key": promotion.param_key,
                "param_value": promotion.param_value,
                "valid_from": promotion.valid_from,
                "valid_until": promotion.valid_until,
                "is_active": promotion.is_active,
            }
        )


class ListStorePromotionsUseCase(_StorePromotionOwnershipMixin):
    def __init__(
        self,
        promotion_repository,
        store_repository: DjangoStoreRepository,
        product_repository: DjangoProductRepository,
    ) -> None:
        self._promotion_repository = promotion_repository
        self._store_repository = store_repository
        self._product_repository = product_repository

    def execute(self, *, store_id: int, owner_id: int) -> list[StorePromotion]:
        self._ensure_store_owner(store_id, owner_id)
        return self._promotion_repository.list_by_store(store_id)


class UpdateStorePromotionUseCase(_StorePromotionOwnershipMixin):
    def __init__(
        self,
        promotion_repository,
        store_repository: DjangoStoreRepository,
        product_repository: DjangoProductRepository,
    ) -> None:
        self._promotion_repository = promotion_repository
        self._store_repository = store_repository
        self._product_repository = product_repository

    def execute(self, dto: UpdateStorePromotionDTO) -> StorePromotion:
        self._ensure_store_owner(dto.store_id, dto.owner_id)

        promotion = self._promotion_repository.get_by_id(dto.promotion_id)
        if promotion is None or promotion.store_id != dto.store_id:
            raise StorePromotionNotFoundError(
                f"Promoción {dto.promotion_id} no encontrada"
            )

        update_data: dict = {}
        if dto.name is not None:
            StorePromotion(
                store_id=dto.store_id,
                name=dto.name.strip(),
                discount_type=dto.discount_type or promotion.discount_type,
                discount_value=dto.discount_value or promotion.discount_value,
            )
            update_data["name"] = dto.name.strip()
        if dto.discount_type is not None:
            update_data["discount_type"] = dto.discount_type.value
        if dto.discount_value is not None:
            StorePromotion(
                store_id=dto.store_id,
                name=dto.name or promotion.name,
                discount_type=dto.discount_type or promotion.discount_type,
                discount_value=dto.discount_value,
            )
            update_data["discount_value"] = dto.discount_value

        next_product_id = (
            dto.product_id if dto.product_id is not None else promotion.product_id
        )
        next_variant_id = (
            dto.variant_id if dto.variant_id is not None else promotion.variant_id
        )
        next_param_key = (
            dto.param_key if dto.param_key is not None else promotion.param_key
        )
        next_param_value = (
            dto.param_value if dto.param_value is not None else promotion.param_value
        )

        if (
            dto.product_id is not None
            or dto.variant_id is not None
            or dto.param_key is not None
            or dto.param_value is not None
        ):
            resolved_product_id, resolved_variant_id = self._resolve_product_and_variant(
                dto.store_id,
                next_product_id,
                next_variant_id if not next_param_key else None,
            )
            resolved_param_key, resolved_param_value = self._validate_product_param(
                resolved_product_id,
                next_param_key,
                next_param_value,
            )
            if resolved_param_key:
                resolved_variant_id = None
            self._validate_product(dto.store_id, resolved_product_id)
            update_data["product_id"] = resolved_product_id
            update_data["variant_id"] = resolved_variant_id
            update_data["param_key"] = resolved_param_key
            update_data["param_value"] = resolved_param_value

        if dto.valid_from is not UNSET:
            update_data["valid_from"] = dto.valid_from
        if dto.valid_until is not UNSET:
            update_data["valid_until"] = dto.valid_until
        if dto.is_active is not None:
            update_data["is_active"] = dto.is_active

        return self._promotion_repository.update(dto.promotion_id, update_data)


class DeactivateStorePromotionUseCase(_StorePromotionOwnershipMixin):
    def __init__(
        self,
        promotion_repository,
        store_repository: DjangoStoreRepository,
        product_repository: DjangoProductRepository,
    ) -> None:
        self._promotion_repository = promotion_repository
        self._store_repository = store_repository
        self._product_repository = product_repository

    def execute(self, dto: DeactivateStorePromotionDTO) -> StorePromotion:
        self._ensure_store_owner(dto.store_id, dto.owner_id)

        promotion = self._promotion_repository.get_by_id(dto.promotion_id)
        if promotion is None or promotion.store_id != dto.store_id:
            raise StorePromotionNotFoundError(
                f"Promoción {dto.promotion_id} no encontrada"
            )

        return self._promotion_repository.deactivate(dto.promotion_id)
