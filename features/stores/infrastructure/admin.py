from django.contrib import admin

from core.admin_media import admin_image_preview
from features.stores.infrastructure.models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """Sin GISModelAdmin: evita dependencia de OpenLayers en Docker."""

    list_display = (
        "name",
        "owner",
        "status",
        "logo_preview",
        "display_coords",
        "address",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("name", "owner__username", "address")
    raw_id_fields = ("owner",)
    readonly_fields = ("display_coords", "logo_preview_large", "created_at", "updated_at")
    exclude = ("location",)
    fields = (
        "owner",
        "name",
        "status",
        "vertical",
        "address",
        "description",
        "phone",
        "logo",
        "logo_preview_large",
        "is_active",
        "display_coords",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Logo")
    def logo_preview(self, obj: Store) -> str:
        if not obj.logo:
            return "—"
        return admin_image_preview(obj.logo.url, max_height=40, max_width=40)

    @admin.display(description="Vista previa del logo")
    def logo_preview_large(self, obj: Store) -> str:
        if not obj.logo:
            return "Sin logo"
        return admin_image_preview(obj.logo.url, max_height=160, max_width=160)

    @admin.display(description="Coordenadas (lat, lon)")
    def display_coords(self, obj: Store) -> str:
        if obj.location is None:
            return "—"
        return f"{obj.location.y:.6f}, {obj.location.x:.6f}"
