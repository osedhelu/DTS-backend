from django.db import models

from features.marketing.domain.entities import DiscountType


class CouponModel(models.Model):
    code = models.CharField(max_length=64, unique=True)
    discount_type = models.CharField(
        max_length=10,
        choices=[(discount_type.value, discount_type.value) for discount_type in DiscountType],
    )
    discount_value = models.DecimalField(max_digits=12, decimal_places=2)
    min_order_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "marketing_coupon"
        verbose_name = "cupón"
        verbose_name_plural = "cupones"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code


class BannerModel(models.Model):
    title = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500)
    link_url = models.URLField(max_length=500, blank=True, default="")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "marketing_banner"
        verbose_name = "banner"
        verbose_name_plural = "banners"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.title


class StorePromotionModel(models.Model):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="promotions",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions",
    )
    param_key = models.CharField(max_length=100, blank=True, null=True)
    param_value = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    discount_type = models.CharField(
        max_length=10,
        choices=[(discount_type.value, discount_type.value) for discount_type in DiscountType],
    )
    discount_value = models.DecimalField(max_digits=12, decimal_places=2)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "marketing_store_promotion"
        verbose_name = "promoción de tienda"
        verbose_name_plural = "promociones de tienda"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
