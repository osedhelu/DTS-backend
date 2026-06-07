from rest_framework import serializers

from features.marketing.domain.entities import DiscountType
from features.marketing.infrastructure.models import BannerModel, CouponModel


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponModel
        fields = [
            "id",
            "code",
            "discount_type",
            "discount_value",
            "min_order_total",
            "max_uses",
            "used_count",
            "valid_from",
            "valid_until",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "used_count", "created_at", "updated_at"]

    def validate_discount_type(self, value: str) -> str:
        if value not in {discount_type.value for discount_type in DiscountType}:
            raise serializers.ValidationError("Tipo de descuento inválido")
        return value

    def validate(self, attrs: dict) -> dict:
        discount_type = attrs.get(
            "discount_type",
            getattr(self.instance, "discount_type", None),
        )
        discount_value = attrs.get(
            "discount_value",
            getattr(self.instance, "discount_value", None),
        )
        valid_from = attrs.get("valid_from", getattr(self.instance, "valid_from", None))
        valid_until = attrs.get(
            "valid_until",
            getattr(self.instance, "valid_until", None),
        )

        if discount_value is not None and discount_value <= 0:
            raise serializers.ValidationError(
                {"discount_value": "El valor de descuento debe ser positivo"}
            )

        if (
            discount_type == DiscountType.PERCENTAGE.value
            and discount_value is not None
            and discount_value > 100
        ):
            raise serializers.ValidationError(
                {"discount_value": "El descuento porcentual no puede superar 100"}
            )

        if valid_from is not None and valid_until is not None and valid_until < valid_from:
            raise serializers.ValidationError(
                {"valid_until": "Debe ser posterior a valid_from"}
            )

        return attrs


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerModel
        fields = [
            "id",
            "title",
            "image_url",
            "link_url",
            "is_active",
            "sort_order",
        ]
        read_only_fields = fields
