from rest_framework import serializers

from features.products.domain.entities import ProductType


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    store_id = serializers.IntegerField(read_only=True)
    product_type = serializers.ChoiceField(choices=[t.value for t in ProductType])
    category_id = serializers.IntegerField(allow_null=True, required=False)
    subcategory_id = serializers.IntegerField(allow_null=True, required=False)
    stock = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(read_only=True)
    requires_on_site_visit = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.IntegerField(allow_null=True, required=False)
    tracks_stock = serializers.BooleanField(read_only=True)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "name": instance.name,
            "price": str(instance.price),
            "store_id": instance.store_id,
            "product_type": instance.product_type,
            "category_id": instance.category_id,
            "subcategory_id": instance.subcategory_id,
            "stock": instance.stock,
            "description": instance.description,
            "is_active": instance.is_active,
            "requires_on_site_visit": instance.requires_on_site_visit,
            "duration_minutes": instance.duration_minutes,
            "tracks_stock": instance.tracks_stock,
        }


class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock = serializers.IntegerField(min_value=0, default=0, required=False)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subcategory_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")


class CreateServiceSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subcategory_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    duration_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class CategoryTreeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subcategories = serializers.ListField(child=serializers.DictField())


class CreateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class CreateSubcategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    parent_id = serializers.IntegerField()
