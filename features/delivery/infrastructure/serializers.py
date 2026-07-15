from rest_framework import serializers


class TrackingPointSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, allow_null=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)
    sequence = serializers.IntegerField(read_only=True)
    recorded_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "latitude": instance.latitude,
            "longitude": instance.longitude,
            "sequence": instance.sequence,
            "recorded_at": instance.recorded_at.isoformat(),
        }


class DeliveryTrackingSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, allow_null=True)
    order_id = serializers.IntegerField(read_only=True)
    point_count = serializers.IntegerField(read_only=True)
    points = TrackingPointSerializer(many=True, read_only=True)
    order_status = serializers.CharField(read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True, allow_null=True)
    is_live = serializers.BooleanField(read_only=True)
    destination_latitude = serializers.FloatField(read_only=True, allow_null=True)
    destination_longitude = serializers.FloatField(read_only=True, allow_null=True)
    driver_latitude = serializers.FloatField(read_only=True, allow_null=True)
    driver_longitude = serializers.FloatField(read_only=True, allow_null=True)

    def to_representation(self, instance):
        latest = instance.latest_point
        status = getattr(instance, "order_status", None)
        return {
            "id": instance.id,
            "order_id": instance.order_id,
            "point_count": instance.point_count,
            "points": TrackingPointSerializer(instance.points, many=True).data,
            "order_status": status,
            "status": status,
            "is_live": bool(getattr(instance, "is_live", False)),
            "destination_latitude": getattr(instance, "destination_latitude", None),
            "destination_longitude": getattr(instance, "destination_longitude", None),
            "driver_latitude": latest.latitude if latest else None,
            "driver_longitude": latest.longitude if latest else None,
        }


class RecordLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    recorded_at = serializers.DateTimeField(required=False, allow_null=True)


class DriverOfferSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    store_id = serializers.IntegerField()
    store_name = serializers.CharField()
    store_latitude = serializers.FloatField()
    store_longitude = serializers.FloatField()
    total = serializers.CharField()
    distance_km = serializers.FloatField()
    status = serializers.CharField()


class AcceptOfferResponseSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    driver_id = serializers.IntegerField()
    status = serializers.CharField()
