from django.db import models

from features.products.domain.entities import (
    Category,
    Product,
    ProductImage,
    ProductIngredient,
    ProductType,
    ProductVariant,
)
from features.products.infrastructure.models import Category as CategoryModel
from features.products.infrastructure.models import Product as ProductModel
from features.products.infrastructure.models import ProductImage as ProductImageModel
from features.products.infrastructure.models import ProductIngredient as ProductIngredientModel
from features.products.infrastructure.models import ProductVariant as ProductVariantModel


def _category_to_entity(model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        name=model.name,
        store_id=model.store_id,
        parent_id=model.parent_id,
        field_config=model.field_config or {},
    )


def _product_to_entity(model: ProductModel) -> Product:
    return Product(
        id=model.id,
        name=model.name,
        price=model.price,
        store_id=model.store_id,
        product_type=ProductType(model.product_type),
        category_id=model.category_id,
        subcategory_id=model.subcategory_id,
        stock=model.stock,
        description=model.description,
        is_active=model.is_active,
        requires_on_site_visit=model.requires_on_site_visit,
        duration_minutes=model.duration_minutes,
        dynamic_values=model.dynamic_values or {},
    )


def _variant_to_entity(model: ProductVariantModel) -> ProductVariant:
    return ProductVariant(
        id=model.id,
        product_id=model.product_id,
        name=model.name,
        price=model.price,
        sort_order=model.sort_order,
    )


def _ingredient_to_entity(model: ProductIngredientModel) -> ProductIngredient:
    return ProductIngredient(
        id=model.id,
        product_id=model.product_id,
        name=model.name,
        is_allergen=model.is_allergen,
    )


def _image_to_entity(model: ProductImageModel) -> ProductImage:
    return ProductImage(
        id=model.id,
        product_id=model.product_id,
        image_path=model.image.url if model.image else "",
        is_primary=model.is_primary,
    )


class DjangoCategoryRepository:
    def create(self, data: dict) -> Category:
        model = CategoryModel.objects.create(
            store_id=data["store_id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            field_config=data.get("field_config") or {},
        )
        return _category_to_entity(model)

    def get_by_id(self, category_id: int) -> Category | None:
        try:
            return _category_to_entity(CategoryModel.objects.get(pk=category_id))
        except CategoryModel.DoesNotExist:
            return None

    def list_tree_by_store(self, store_id: int) -> list[dict]:
        roots = CategoryModel.objects.filter(
            store_id=store_id,
            parent__isnull=True,
        ).prefetch_related("subcategories")

        return [
            {
                "id": root.id,
                "name": root.name,
                "field_config": root.field_config or {},
                "subcategories": [
                    {
                        "id": sub.id,
                        "name": sub.name,
                        "parent_id": sub.parent_id,
                        "field_config": sub.field_config or {},
                    }
                    for sub in root.subcategories.all()
                ],
            }
            for root in roots
        ]

    def update(self, category_id: int, data: dict) -> Category:
        model = CategoryModel.objects.get(pk=category_id)
        update_fields = ["updated_at"]
        if "name" in data:
            model.name = data["name"]
            update_fields.append("name")
        if "field_config" in data:
            model.field_config = data["field_config"]
            update_fields.append("field_config")
        model.save(update_fields=update_fields)
        return _category_to_entity(model)

    def delete(self, category_id: int) -> None:
        CategoryModel.objects.filter(pk=category_id).delete()

    def count_products(self, category_id: int) -> int:
        return ProductModel.objects.filter(
            models.Q(category_id=category_id) | models.Q(subcategory_id=category_id)
        ).count()

    def count_subcategories(self, category_id: int) -> int:
        return CategoryModel.objects.filter(parent_id=category_id).count()


class DjangoProductRepository:
    def create(self, data: dict) -> Product:
        model = ProductModel.objects.create(
            store_id=data["store_id"],
            name=data["name"],
            price=data["price"],
            stock=data.get("stock", 0),
            category_id=data.get("category_id"),
            subcategory_id=data.get("subcategory_id"),
            description=data.get("description", ""),
            product_type=data["product_type"],
            requires_on_site_visit=data.get("requires_on_site_visit", False),
            duration_minutes=data.get("duration_minutes"),
            is_active=data.get("is_active", True),
            dynamic_values=data.get("dynamic_values") or {},
        )
        return _product_to_entity(model)

    def get_by_id(self, product_id: int) -> Product | None:
        try:
            return _product_to_entity(ProductModel.objects.get(pk=product_id))
        except ProductModel.DoesNotExist:
            return None

    def deactivate(self, product_id: int) -> Product:
        model = ProductModel.objects.get(pk=product_id)
        model.is_active = False
        model.save(update_fields=["is_active", "updated_at"])
        return _product_to_entity(model)

    def update_stock(self, product_id: int, stock: int) -> Product:
        model = ProductModel.objects.get(pk=product_id)
        model.stock = stock
        model.save(update_fields=["stock", "updated_at"])
        return _product_to_entity(model)

    def update(self, product_id: int, data: dict) -> Product:
        model = ProductModel.objects.get(pk=product_id)
        update_fields = ["updated_at"]
        for field in (
            "name",
            "price",
            "description",
            "stock",
            "category_id",
            "subcategory_id",
            "duration_minutes",
            "dynamic_values",
        ):
            if field in data:
                setattr(model, field, data[field])
                update_fields.append(field)
        model.save(update_fields=update_fields)
        return _product_to_entity(model)

    def list_variants(self, product_id: int) -> list[ProductVariant]:
        return [
            _variant_to_entity(model)
            for model in ProductVariantModel.objects.filter(product_id=product_id)
        ]

    def replace_variants(self, product_id: int, variants: list[dict]) -> list[ProductVariant]:
        ProductVariantModel.objects.filter(product_id=product_id).delete()
        created: list[ProductVariant] = []
        for index, variant in enumerate(variants):
            model = ProductVariantModel.objects.create(
                product_id=product_id,
                name=variant["name"],
                price=variant["price"],
                sort_order=variant.get("sort_order", index),
            )
            created.append(_variant_to_entity(model))
        return created

    def list_ingredients(self, product_id: int) -> list[ProductIngredient]:
        return [
            _ingredient_to_entity(model)
            for model in ProductIngredientModel.objects.filter(product_id=product_id)
        ]

    def replace_ingredients(self, product_id: int, ingredients: list[dict]) -> list[ProductIngredient]:
        ProductIngredientModel.objects.filter(product_id=product_id).delete()
        created: list[ProductIngredient] = []
        for ingredient in ingredients:
            model = ProductIngredientModel.objects.create(
                product_id=product_id,
                name=ingredient["name"],
                is_allergen=ingredient.get("is_allergen", False),
            )
            created.append(_ingredient_to_entity(model))
        return created

    def list_images(self, product_id: int) -> list[ProductImage]:
        return [
            _image_to_entity(model)
            for model in ProductImageModel.objects.filter(product_id=product_id)
        ]

    def add_image(self, product_id: int, image_file, *, is_primary: bool = False) -> ProductImage:
        if is_primary:
            ProductImageModel.objects.filter(product_id=product_id).update(is_primary=False)
        model = ProductImageModel.objects.create(
            product_id=product_id,
            image=image_file,
            is_primary=is_primary,
        )
        return _image_to_entity(model)

    def get_image(self, image_id: int) -> ProductImage | None:
        try:
            return _image_to_entity(ProductImageModel.objects.get(pk=image_id))
        except ProductImageModel.DoesNotExist:
            return None

    def delete_image(self, image_id: int) -> None:
        model = ProductImageModel.objects.get(pk=image_id)
        was_primary = model.is_primary
        product_id = model.product_id
        model.delete()
        if was_primary:
            next_image = ProductImageModel.objects.filter(product_id=product_id).first()
            if next_image is not None:
                next_image.is_primary = True
                next_image.save(update_fields=["is_primary", "updated_at"])

    def update_image(
        self,
        image_id: int,
        *,
        is_primary: bool | None = None,
        image_file=None,
    ) -> ProductImage:
        model = ProductImageModel.objects.get(pk=image_id)
        update_fields = ["updated_at"]

        if is_primary is True:
            ProductImageModel.objects.filter(product_id=model.product_id).update(
                is_primary=False,
            )
            model.is_primary = True
            update_fields.append("is_primary")
        elif is_primary is False:
            model.is_primary = False
            update_fields.append("is_primary")

        if image_file is not None:
            model.image = image_file
            update_fields.append("image")

        model.save(update_fields=update_fields)
        return _image_to_entity(model)

    def list_by_store(
        self,
        store_id: int,
        *,
        product_type: ProductType | None = None,
        category_id: int | None = None,
        subcategory_id: int | None = None,
        search: str | None = None,
        active_only: bool = True,
    ) -> list[Product]:
        queryset = ProductModel.objects.filter(store_id=store_id).order_by("name")

        if active_only:
            queryset = queryset.filter(is_active=True)
        if product_type is not None:
            queryset = queryset.filter(product_type=product_type.value)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if subcategory_id is not None:
            queryset = queryset.filter(subcategory_id=subcategory_id)
        if search:
            queryset = queryset.filter(name__icontains=search.strip())

        return [_product_to_entity(model) for model in queryset]
