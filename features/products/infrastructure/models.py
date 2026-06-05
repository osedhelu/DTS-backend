from django.db import models

from features.products.domain.entities import ProductType
from features.stores.infrastructure.models import Store


class Category(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_category"
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name", "parent"],
                name="unique_category_name_per_parent",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    @property
    def is_subcategory(self) -> bool:
        return self.parent_id is not None


class Product(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    subcategory = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products_as_subcategory",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    product_type = models.CharField(
        max_length=10,
        choices=[(product_type.value, product_type.value) for product_type in ProductType],
        default=ProductType.PHYSICAL,
    )
    requires_on_site_visit = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_product"
        verbose_name = "producto"
        verbose_name_plural = "productos"
        indexes = [
            models.Index(fields=["store", "product_type"], name="products_store_type_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def tracks_stock(self) -> bool:
        return self.product_type == ProductType.PHYSICAL
