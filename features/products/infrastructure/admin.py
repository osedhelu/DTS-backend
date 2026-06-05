from django.contrib import admin

from features.products.infrastructure.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "parent")
    list_filter = ("store",)
    search_fields = ("name",)
    raw_id_fields = ("store", "parent")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "product_type", "price", "stock", "is_active")
    list_filter = ("product_type", "is_active", "store")
    search_fields = ("name", "description")
    raw_id_fields = ("store", "category", "subcategory")
