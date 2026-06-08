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
    dynamic_values = serializers.JSONField(required=False)

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
            "dynamic_values": instance.dynamic_values or {},
        }


class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock = serializers.IntegerField(min_value=0, default=0, required=False)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subcategory_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    dynamic_values = serializers.JSONField(required=False)


class UpdateStockSerializer(serializers.Serializer):
    stock = serializers.IntegerField(min_value=0)


class ProductVariantSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, required=False)
    name = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    sort_order = serializers.IntegerField(min_value=0, default=0, required=False)


class ProductIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, required=False)
    name = serializers.CharField(max_length=255)
    is_allergen = serializers.BooleanField(default=False, required=False)


class ProductImageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.CharField(read_only=True)
    is_primary = serializers.BooleanField()


class UpdateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    stock = serializers.IntegerField(min_value=0, required=False)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subcategory_id = serializers.IntegerField(required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    variants = ProductVariantSerializer(many=True, required=False)
    ingredients = ProductIngredientSerializer(many=True, required=False)
    dynamic_values = serializers.JSONField(required=False)


class ProductDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    store_id = serializers.IntegerField()
    product_type = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    subcategory_id = serializers.IntegerField(allow_null=True)
    stock = serializers.IntegerField()
    description = serializers.CharField()
    is_active = serializers.BooleanField()
    requires_on_site_visit = serializers.BooleanField()
    duration_minutes = serializers.IntegerField(allow_null=True)
    tracks_stock = serializers.BooleanField()
    variants = ProductVariantSerializer(many=True)
    ingredients = ProductIngredientSerializer(many=True)
    images = ProductImageSerializer(many=True)

    def to_representation(self, instance):
        from core.media_urls import build_public_media_url

        product = instance.product if hasattr(instance, "product") else instance
        variants = getattr(instance, "variants", [])
        ingredients = getattr(instance, "ingredients", [])
        images = getattr(instance, "images", [])

        return {
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "store_id": product.store_id,
            "product_type": product.product_type,
            "category_id": product.category_id,
            "subcategory_id": product.subcategory_id,
            "stock": product.stock,
            "description": product.description,
            "is_active": product.is_active,
            "requires_on_site_visit": product.requires_on_site_visit,
            "duration_minutes": product.duration_minutes,
            "tracks_stock": product.tracks_stock,
            "dynamic_values": product.dynamic_values or {},
            "variants": [
                {
                    "id": variant.id,
                    "name": variant.name,
                    "price": str(variant.price),
                    "sort_order": variant.sort_order,
                }
                for variant in variants
            ],
            "ingredients": [
                {
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "is_allergen": ingredient.is_allergen,
                }
                for ingredient in ingredients
            ],
            "images": [
                {
                    "id": image.id,
                    "url": build_public_media_url(image.image_path),
                    "is_primary": image.is_primary,
                }
                for image in images
            ],
        }


class ReplaceVariantsSerializer(serializers.Serializer):
    variants = ProductVariantSerializer(many=True)


class ReplaceIngredientsSerializer(serializers.Serializer):
    ingredients = ProductIngredientSerializer(many=True)


class UploadProductImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
    is_primary = serializers.BooleanField(default=False, required=False)


class CreateServiceSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subcategory_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    duration_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    dynamic_values = serializers.JSONField(required=False)


class CategoryTreeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subcategories = serializers.ListField(child=serializers.DictField())


class CreateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class CreateSubcategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    parent_id = serializers.IntegerField()


class UpdateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    field_config = serializers.DictField(required=False)
