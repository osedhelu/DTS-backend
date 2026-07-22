from rest_framework import serializers


class CartItemUpsertSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    replace_store = serializers.BooleanField(required=False, default=True)


class CartItemQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class CartItemResponseSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.CharField()
    quantity = serializers.IntegerField()
    notes = serializers.CharField(allow_blank=True)
    store_id = serializers.IntegerField()
    product_type = serializers.CharField()
    primary_image_url = serializers.CharField(allow_null=True, required=False)
    stock = serializers.IntegerField()


class CartResponseSerializer(serializers.Serializer):
    store_id = serializers.IntegerField(allow_null=True)
    store_name = serializers.CharField(allow_blank=True)
    items = CartItemResponseSerializer(many=True)
    item_count = serializers.IntegerField()
    total = serializers.CharField()
