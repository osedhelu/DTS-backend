from features.marketing.domain.entities import DiscountType, StorePromotion
from features.marketing.infrastructure.models import StorePromotionModel


def _to_entity(model: StorePromotionModel) -> StorePromotion:
    return StorePromotion(
        id=model.id,
        store_id=model.store_id,
        name=model.name,
        discount_type=DiscountType(model.discount_type),
        discount_value=model.discount_value,
        product_id=model.product_id,
        valid_from=model.valid_from,
        valid_until=model.valid_until,
        is_active=model.is_active,
    )


class DjangoStorePromotionRepository:
    def create(self, data: dict) -> StorePromotion:
        model = StorePromotionModel.objects.create(
            store_id=data["store_id"],
            name=data["name"],
            discount_type=data["discount_type"],
            discount_value=data["discount_value"],
            product_id=data.get("product_id"),
            valid_from=data.get("valid_from"),
            valid_until=data.get("valid_until"),
            is_active=data.get("is_active", True),
        )
        return _to_entity(model)

    def get_by_id(self, promotion_id: int) -> StorePromotion | None:
        try:
            return _to_entity(StorePromotionModel.objects.get(pk=promotion_id))
        except StorePromotionModel.DoesNotExist:
            return None

    def list_by_store(self, store_id: int, *, active_only: bool = False) -> list[StorePromotion]:
        queryset = StorePromotionModel.objects.filter(store_id=store_id).order_by("-created_at")
        if active_only:
            queryset = queryset.filter(is_active=True)
        return [_to_entity(model) for model in queryset]

    def update(self, promotion_id: int, data: dict) -> StorePromotion:
        model = StorePromotionModel.objects.get(pk=promotion_id)
        update_fields = ["updated_at"]
        for field in (
            "name",
            "discount_type",
            "discount_value",
            "product_id",
            "valid_from",
            "valid_until",
            "is_active",
        ):
            if field in data:
                setattr(model, field, data[field])
                update_fields.append(field)
        model.save(update_fields=update_fields)
        return _to_entity(model)

    def deactivate(self, promotion_id: int) -> StorePromotion:
        model = StorePromotionModel.objects.get(pk=promotion_id)
        model.is_active = False
        model.save(update_fields=["is_active", "updated_at"])
        return _to_entity(model)
