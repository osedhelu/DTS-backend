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

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "order_id": instance.order_id,
            "point_count": instance.point_count,
            "points": TrackingPointSerializer(instance.points, many=True).data,
        }


class RecordLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    recorded_at = serializers.DateTimeField(required=False, allow_null=True)
