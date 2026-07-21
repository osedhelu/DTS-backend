from rest_framework import serializers

from features.payments.domain.entities import PaymentMethodType


class StorePaymentMethodSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    method_type = serializers.ChoiceField(choices=[t.value for t in PaymentMethodType])
    name = serializers.CharField(max_length=100)
    instructions = serializers.CharField(required=False, allow_blank=True)
    qr_image_url = serializers.CharField(read_only=True, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0, required=False)


class CreateStorePaymentMethodSerializer(serializers.Serializer):
    method_type = serializers.ChoiceField(choices=[t.value for t in PaymentMethodType])
    name = serializers.CharField(max_length=100)
    instructions = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0, required=False)
    qr_image = serializers.ImageField(required=False, allow_null=True)


class UpdateStorePaymentMethodSerializer(serializers.Serializer):
    method_type = serializers.ChoiceField(
        choices=[t.value for t in PaymentMethodType], required=False
    )
    name = serializers.CharField(max_length=100, required=False)
    instructions = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    sort_order = serializers.IntegerField(required=False)
    qr_image = serializers.ImageField(required=False, allow_null=True)


class ConfirmPaymentSerializer(serializers.Serializer):
    payment_reference = serializers.CharField(required=False, allow_blank=True, default="")


def serialize_payment_method(method) -> dict:
    from core.media_urls import build_public_media_url

    return {
        "id": method.id,
        "method_type": method.method_type,
        "name": method.name,
        "instructions": method.instructions,
        "qr_image_url": build_public_media_url(
            method.qr_image.url if method.qr_image else ""
        ),
        "is_active": method.is_active,
        "sort_order": method.sort_order,
    }
