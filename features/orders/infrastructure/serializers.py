from rest_framework import serializers

from features.orders.domain.value_objects import OrderStatus


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
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "customer_id": instance.customer_id,
            "store_id": instance.store_id,
            "driver_id": instance.driver_id,
            "status": instance.status,
            "total": str(instance.total),
            "item_count": instance.item_count,
            "items": OrderItemSerializer(instance.items, many=True).data,
        }


class CreateOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = CreateOrderItemSerializer(many=True)


class TransitionOrderSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[status.value for status in OrderStatus])
