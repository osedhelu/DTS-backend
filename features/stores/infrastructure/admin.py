from django.contrib import admin

from features.stores.infrastructure.models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """Sin GISModelAdmin: evita dependencia de OpenLayers en Docker."""

    list_display = ("name", "owner", "status", "display_coords", "address", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "owner__username", "address")
    raw_id_fields = ("owner",)
    readonly_fields = ("display_coords",)
    exclude = ("location",)

    @admin.display(description="Coordenadas (lat, lon)")
    def display_coords(self, obj: Store) -> str:
        if obj.location is None:
            return "—"
        return f"{obj.location.y:.6f}, {obj.location.x:.6f}"
