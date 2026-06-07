from rest_framework import serializers

from features.orders.domain.value_objects import OrderStatus, OrderType


class OrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(allow_null=True)
    product_name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "product_id": instance.product_id,
            "product_name": instance.product_name,
            "unit_price": str(instance.unit_price),
            "quantity": instance.quantity,
            "subtotal": str(instance.subtotal),
        }


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(read_only=True)
    store_id = serializers.IntegerField(read_only=True)
    driver_id = serializers.IntegerField(read_only=True, allow_null=True)
    status = serializers.ChoiceField(choices=[status.value for status in OrderStatus])
    order_type = serializers.ChoiceField(choices=[order_type.value for order_type in OrderType])
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    service_address = serializers.CharField(read_only=True, allow_null=True)
    customer_notes = serializers.CharField(read_only=True, allow_null=True)
    scheduled_at = serializers.DateTimeField(read_only=True, allow_null=True)
    service_latitude = serializers.FloatField(read_only=True, allow_null=True)
    service_longitude = serializers.FloatField(read_only=True, allow_null=True)
    duration_minutes = serializers.IntegerField(read_only=True, allow_null=True)

    def to_representation(self, instance):
        service = instance.service_details
        return {
            "id": instance.id,
            "customer_id": instance.customer_id,
            "store_id": instance.store_id,
            "driver_id": instance.driver_id,
            "status": instance.status,
            "order_type": instance.order_type,
            "total": str(instance.total),
            "item_count": instance.item_count,
            "items": OrderItemSerializer(instance.items, many=True).data,
            "service_address": service.service_address if service else None,
            "customer_notes": service.customer_notes if service else None,
            "scheduled_at": service.scheduled_at if service else None,
            "service_latitude": service.latitude if service else None,
            "service_longitude": service.longitude if service else None,
            "duration_minutes": service.duration_minutes if service else None,
        }


class CreateOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = CreateOrderItemSerializer(many=True)


class CreateServiceOrderSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = CreateOrderItemSerializer(many=True)
    service_address = serializers.CharField(trim_whitespace=False, allow_blank=True)
    customer_notes = serializers.CharField(required=False, allow_blank=True, default="")
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    def validate_service_address(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("La dirección del servicio es obligatoria")
        return value.strip()


class TransitionOrderSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[status.value for status in OrderStatus])
