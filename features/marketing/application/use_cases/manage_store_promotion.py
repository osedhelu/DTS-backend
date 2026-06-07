from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from features.marketing.domain.entities import DiscountType, StorePromotion
from features.marketing.domain.exceptions import (
    InvalidStorePromotionError,
    StorePromotionNotFoundError,
)
from features.products.domain.exceptions import ProductNotFoundError
from features.products.infrastructure.repositories import DjangoProductRepository
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.infrastructure.repositories import DjangoStoreRepository


@dataclass(frozen=True)
class CreateStorePromotionDTO:
    store_id: int
    owner_id: int
    name: str
    discount_type: DiscountType
    discount_value: Decimal
    product_id: int | None = None
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
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class DeactivateStorePromotionDTO:
    promotion_id: int
    store_id: int
    owner_id: int


class StorePromotionNotFoundError(InvalidStorePromotionError):
    pass


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
        self._validate_product(dto.store_id, dto.product_id)

        promotion = StorePromotion(
            store_id=dto.store_id,
            name=dto.name.strip(),
            discount_type=dto.discount_type,
            discount_value=dto.discount_value,
            product_id=dto.product_id,
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

        if dto.product_id is not None:
            self._validate_product(dto.store_id, dto.product_id)

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
        if dto.product_id is not None:
            update_data["product_id"] = dto.product_id
        if dto.valid_from is not None:
            update_data["valid_from"] = dto.valid_from
        if dto.valid_until is not None:
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
