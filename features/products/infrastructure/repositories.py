from features.products.domain.entities import Category, Product, ProductType
from features.products.infrastructure.models import Category as CategoryModel
from features.products.infrastructure.models import Product as ProductModel


def _category_to_entity(model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        name=model.name,
        store_id=model.store_id,
        parent_id=model.parent_id,
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
    )


class DjangoCategoryRepository:
    def create(self, data: dict) -> Category:
        model = CategoryModel.objects.create(
            store_id=data["store_id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
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
                "subcategories": [
                    {
                        "id": sub.id,
                        "name": sub.name,
                        "parent_id": sub.parent_id,
                    }
                    for sub in root.subcategories.all()
                ],
            }
            for root in roots
        ]


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

    def list_by_store(
        self,
        store_id: int,
        *,
        product_type: ProductType | None = None,
        category_id: int | None = None,
        subcategory_id: int | None = None,
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

        return [_product_to_entity(model) for model in queryset]
