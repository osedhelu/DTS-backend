from django.contrib import admin

from core.admin_media import admin_image_preview
from features.products.infrastructure.models import Category, Product, ProductImage
from features.products.infrastructure.models import CategoryImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image_preview", "image", "is_primary", "created_at")
    readonly_fields = ("image_preview", "created_at")
    ordering = ("-is_primary", "id")

    @admin.display(description="Vista previa")
    def image_preview(self, obj: ProductImage) -> str:
        if not obj.image:
            return "—"
        return admin_image_preview(obj.image.url, max_height=64, max_width=64)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "image_preview", "product", "is_primary", "created_at")
    list_filter = ("is_primary", "product__store")
    search_fields = ("product__name", "product__store__name")
    raw_id_fields = ("product",)
    readonly_fields = ("image_preview_large", "created_at", "updated_at")
    fields = (
        "product",
        "image",
        "image_preview_large",
        "is_primary",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    @admin.display(description="Miniatura")
    def image_preview(self, obj: ProductImage) -> str:
        if not obj.image:
            return "—"
        return admin_image_preview(obj.image.url, max_height=48, max_width=48)

    @admin.display(description="Vista previa")
    def image_preview_large(self, obj: ProductImage) -> str:
        if not obj.image:
            return "—"
        return admin_image_preview(obj.image.url, max_height=240, max_width=240)


class CategoryImageInline(admin.TabularInline):
    model = CategoryImage
    extra = 0
    fields = ("image_preview", "image", "is_primary", "created_at")
    readonly_fields = ("image_preview", "created_at")
    ordering = ("-is_primary", "id")

    @admin.display(description="Vista previa")
    def image_preview(self, obj: CategoryImage) -> str:
        if not obj.image:
            return "—"
        return admin_image_preview(obj.image.url, max_height=64, max_width=64)


@admin.register(CategoryImage)
class CategoryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "image_preview", "category", "is_primary", "created_at")
    list_filter = ("is_primary", "category__store")
    search_fields = ("category__name", "category__store__name")
    raw_id_fields = ("category",)
    readonly_fields = ("image_preview_large", "created_at", "updated_at")

    @admin.display(description="Miniatura")
    def image_preview(self, obj: CategoryImage) -> str:
        if not obj.image:
            return "—"
        return admin_image_preview(obj.image.url, max_height=48, max_width=48)

    @admin.display(description="Vista previa")
    def image_preview_large(self, obj: CategoryImage) -> str:
        if not obj.image:
            return "—"
        return admin_image_preview(obj.image.url, max_height=240, max_width=240)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "parent", "image_count")
    list_filter = ("store",)
    search_fields = ("name",)
    raw_id_fields = ("store", "parent")
    inlines = (CategoryImageInline,)

    @admin.display(description="Fotos")
    def image_count(self, obj: Category) -> int:
        return obj.images.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "product_type", "price", "stock", "is_active", "image_count")
    list_filter = ("product_type", "is_active", "store")
    search_fields = ("name", "description")
    raw_id_fields = ("store", "category", "subcategory")
    inlines = (ProductImageInline,)

    @admin.display(description="Fotos")
    def image_count(self, obj: Product) -> int:
        return obj.images.count()
