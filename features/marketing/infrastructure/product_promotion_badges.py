from datetime import datetime

from features.marketing.domain.promotion_display import (
    format_discount_badge,
    promotion_is_currently_active,
    promotion_specificity,
)
from features.marketing.infrastructure.repositories import _to_entity
from features.marketing.infrastructure.models import StorePromotionModel
from features.products.infrastructure.models import ProductVariant


def promotion_badges_for_products(
    store_id: int,
    product_ids: list[int],
    *,
    now: datetime | None = None,
) -> dict[int, str | None]:
    if not product_ids:
        return {}

    promotions = [
        _to_entity(model)
        for model in StorePromotionModel.objects.filter(
            store_id=store_id,
            is_active=True,
        )
    ]

    variant_names = {
        variant.id: variant.name
        for variant in ProductVariant.objects.filter(product_id__in=product_ids)
    }

    badges: dict[int, str | None] = dict.fromkeys(product_ids)
    winners: dict[int, int] = dict.fromkeys(product_ids, 0)

    for promotion in promotions:
        if not promotion_is_currently_active(promotion, now=now):
            continue

        specificity = promotion_specificity(promotion)
        option_label = promotion.param_value
        if promotion.variant_id is not None and not option_label:
            option_label = variant_names.get(promotion.variant_id)
        badge = format_discount_badge(promotion, option_label=option_label)

        if promotion.product_id is None:
            targets = product_ids
        elif promotion.product_id in badges:
            targets = [promotion.product_id]
        else:
            continue

        for product_id in targets:
            if specificity >= winners[product_id]:
                badges[product_id] = badge
                winners[product_id] = specificity

    return badges
