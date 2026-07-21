from rest_framework import serializers


DAY_LABELS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


class OpeningHoursSlotSerializer(serializers.Serializer):
    day_of_week = serializers.IntegerField(min_value=0, max_value=6)
    open_time = serializers.TimeField(required=False, allow_null=True)
    close_time = serializers.TimeField(required=False, allow_null=True)
    is_closed = serializers.BooleanField(default=False)


class OpeningHoursBulkSerializer(serializers.Serializer):
    use_schedule = serializers.BooleanField(required=False)
    slots = OpeningHoursSlotSerializer(many=True)


class DeliveryZoneSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    center_latitude = serializers.FloatField()
    center_longitude = serializers.FloatField()
    radius_km = serializers.DecimalField(max_digits=8, decimal_places=2)
    is_active = serializers.BooleanField(default=True)


class CreateDeliveryZoneSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, default="Principal")
    center_latitude = serializers.FloatField()
    center_longitude = serializers.FloatField()
    radius_km = serializers.DecimalField(max_digits=8, decimal_places=2, default=5)
    is_active = serializers.BooleanField(default=True)


class UpdateDeliveryZoneSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    center_latitude = serializers.FloatField(required=False)
    center_longitude = serializers.FloatField(required=False)
    radius_km = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False
    )
    is_active = serializers.BooleanField(required=False)


class DeliveryCoverageQuerySerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class StorePublicDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
    vertical = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    address = serializers.CharField()
    description = serializers.CharField()
    phone = serializers.CharField()
    logo_url = serializers.CharField()
    is_open = serializers.BooleanField()
    use_schedule = serializers.BooleanField()
    opening_hours = OpeningHoursSlotSerializer(many=True)
    delivery_zones = DeliveryZoneSerializer(many=True)
    accepts_orders = serializers.BooleanField()
    in_delivery_zone = serializers.BooleanField(required=False)
