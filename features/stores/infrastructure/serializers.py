from rest_framework import serializers

from features.stores.domain.entities import StoreStatus


class StoreSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    owner_id = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=[s.value for s in StoreStatus])
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    address = serializers.CharField(required=False, allow_blank=True)
    is_open = serializers.BooleanField(read_only=True)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "name": instance.name,
            "owner_id": instance.owner_id,
            "status": instance.status,
            "latitude": instance.latitude,
            "longitude": instance.longitude,
            "address": instance.address,
            "is_open": instance.is_open,
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
