from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from features.analytics.domain.services import DEFAULT_DRIVER_COMMISSION_RATE
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
            "payment_status": instance.payment_status,
            "payment_method_id": instance.payment_method_id,
            "payment_reference": instance.payment_reference or None,
            "paid_at": instance.paid_at,
            "coupon_code": instance.coupon_code,
            "discount_amount": str(instance.discount_amount),
        }


class CreateOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = CreateOrderItemSerializer(many=True)
    delivery_address = serializers.CharField(required=False, allow_blank=True, default="")
    customer_notes = serializers.CharField(required=False, allow_blank=True, default="")
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    payment_method_id = serializers.IntegerField(required=False, allow_null=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True, default="")


class CreateServiceOrderSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = CreateOrderItemSerializer(many=True)
    service_address = serializers.CharField(trim_whitespace=False, allow_blank=True)
    customer_notes = serializers.CharField(required=False, allow_blank=True, default="")
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    payment_method_id = serializers.IntegerField(required=False, allow_null=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_service_address(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("La dirección del servicio es obligatoria")
        return value.strip()


class DriverOrderDetailSerializer(OrderSerializer):
    store_name = serializers.CharField(read_only=True)
    store_latitude = serializers.FloatField(read_only=True)
    store_longitude = serializers.FloatField(read_only=True)
    store_address = serializers.CharField(read_only=True)
    customer_phone = serializers.CharField(read_only=True, allow_null=True)
    delivery_address = serializers.CharField(read_only=True)
    delivery_latitude = serializers.FloatField(read_only=True, allow_null=True)
    delivery_longitude = serializers.FloatField(read_only=True, allow_null=True)
    driver_earning = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        enrichment = self.context.get("enrichment", {})
        data.update(enrichment)
        return data


def build_driver_order_detail_enrichment(order_model) -> dict:
    store = order_model.store
    service_address = (order_model.service_address or "").strip()
    delivery_address = service_address or store.address or ""
    delivery_latitude = order_model.service_latitude
    delivery_longitude = order_model.service_longitude
    if delivery_latitude is None or delivery_longitude is None:
        delivery_latitude = store.latitude
        delivery_longitude = store.longitude

    customer_phone = None
    customer_profile = getattr(order_model.customer, "customer_profile", None)
    if customer_profile is not None and customer_profile.phone:
        customer_phone = customer_profile.phone

    driver_earning = (
        (order_model.total * DEFAULT_DRIVER_COMMISSION_RATE).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )

    return {
        "store_name": store.name,
        "store_latitude": store.latitude,
        "store_longitude": store.longitude,
        "store_address": store.address,
        "customer_phone": customer_phone,
        "delivery_address": delivery_address,
        "delivery_latitude": delivery_latitude,
        "delivery_longitude": delivery_longitude,
        "driver_earning": str(driver_earning),
    }


class CustomerOrderDetailSerializer(OrderSerializer):
    delivery_address = serializers.CharField(read_only=True)
    delivery_latitude = serializers.FloatField(read_only=True, allow_null=True)
    delivery_longitude = serializers.FloatField(read_only=True, allow_null=True)
    customer_notes = serializers.CharField(read_only=True, allow_null=True)
    driver_name = serializers.CharField(read_only=True, allow_null=True)
    driver_phone = serializers.CharField(read_only=True, allow_null=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        enrichment = self.context.get("enrichment", {})
        data.update(enrichment)
        return data


def build_customer_order_detail_enrichment(order_model) -> dict:
    store = order_model.store
    service_address = (order_model.service_address or "").strip()
    delivery_address = service_address or store.address or ""
    delivery_latitude = order_model.service_latitude
    delivery_longitude = order_model.service_longitude
    if delivery_latitude is None or delivery_longitude is None:
        delivery_latitude = store.latitude
        delivery_longitude = store.longitude

    driver_name = None
    driver_phone = None
    if order_model.driver_id:
        driver_profile = getattr(order_model.driver, "driver_profile", None)
        if driver_profile is not None:
            driver_name = (driver_profile.full_name or "").strip() or order_model.driver.username
            driver_phone = driver_profile.phone or None

    return {
        "delivery_address": delivery_address,
        "delivery_latitude": delivery_latitude,
        "delivery_longitude": delivery_longitude,
        "customer_notes": order_model.customer_notes or None,
        "driver_name": driver_name,
        "driver_phone": driver_phone,
    }


class TransitionOrderSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[status.value for status in OrderStatus])
