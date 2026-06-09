from rest_framework import serializers

from features.stores.domain.entities import StoreStatus, StoreVertical


class StoreSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    owner_id = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=[s.value for s in StoreStatus])
    vertical = serializers.ChoiceField(choices=[v.value for v in StoreVertical])
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    address = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    logo_url = serializers.CharField(required=False, allow_blank=True)
    is_open = serializers.BooleanField(read_only=True)

    def to_representation(self, instance):
        from core.media_urls import build_public_media_url

        return {
            "id": instance.id,
            "name": instance.name,
            "owner_id": instance.owner_id,
            "status": instance.status,
            "vertical": instance.vertical,
            "latitude": instance.latitude,
            "longitude": instance.longitude,
            "address": instance.address,
            "description": instance.description,
            "phone": instance.phone,
            "logo_url": build_public_media_url(instance.logo_url),
            "is_open": instance.is_open,
            "is_active": instance.is_active,
        }


class CreateStoreSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    address = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(
        choices=[s.value for s in StoreStatus],
        default=StoreStatus.CLOSED,
        required=False,
    )


class UpdateStoreStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s.value for s in StoreStatus])


class UpdateStoreProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    address = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=False, min_value=-180, max_value=180)
    status = serializers.ChoiceField(
        choices=[s.value for s in StoreStatus],
        required=False,
    )
    logo = serializers.ImageField(required=False)

    def validate(self, attrs):
        has_lat = "latitude" in attrs
        has_lng = "longitude" in attrs
        if has_lat ^ has_lng:
            raise serializers.ValidationError(
                "Debes enviar latitude y longitude juntos."
            )
        return attrs
