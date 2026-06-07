from rest_framework import serializers

from features.marketing.domain.entities import DiscountType


class StorePromotionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    store_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    discount_type = serializers.ChoiceField(choices=[t.value for t in DiscountType])
    discount_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    product_id = serializers.IntegerField(required=False, allow_null=True)
    valid_from = serializers.DateTimeField(required=False, allow_null=True)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)
    is_active = serializers.BooleanField(read_only=True)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "store_id": instance.store_id,
            "name": instance.name,
            "discount_type": (
                instance.discount_type.value
                if hasattr(instance.discount_type, "value")
                else instance.discount_type
            ),
            "discount_value": str(instance.discount_value),
            "product_id": instance.product_id,
            "valid_from": instance.valid_from,
            "valid_until": instance.valid_until,
            "is_active": instance.is_active,
        }


class CreateStorePromotionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    discount_type = serializers.ChoiceField(choices=[t.value for t in DiscountType])
    discount_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    product_id = serializers.IntegerField(required=False, allow_null=True)
    valid_from = serializers.DateTimeField(required=False, allow_null=True)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)


class UpdateStorePromotionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    discount_type = serializers.ChoiceField(
        choices=[t.value for t in DiscountType],
        required=False,
    )
    discount_value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )
    product_id = serializers.IntegerField(required=False, allow_null=True)
    valid_from = serializers.DateTimeField(required=False, allow_null=True)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
