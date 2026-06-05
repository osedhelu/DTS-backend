from django.contrib import admin

from features.delivery.infrastructure.models import DeliveryTracking, TrackingPoint


class TrackingPointInline(admin.TabularInline):
    model = TrackingPoint
    extra = 0
    readonly_fields = ("sequence", "recorded_at", "display_coords")
    fields = ("sequence", "recorded_at", "display_coords")
    can_delete = False

    @admin.display(description="Coordenadas")
    def display_coords(self, obj: TrackingPoint) -> str:
        if obj.location is None:
            return "—"
        return f"{obj.location.y:.6f}, {obj.location.x:.6f}"


@admin.register(DeliveryTracking)
class DeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = ("order", "created_at", "updated_at")
    search_fields = ("order__id",)
    raw_id_fields = ("order",)
    inlines = (TrackingPointInline,)


@admin.register(TrackingPoint)
class TrackingPointAdmin(admin.ModelAdmin):
    """Sin GISModelAdmin: evita dependencia de OpenLayers en Docker."""

    list_display = ("tracking", "sequence", "recorded_at", "display_coords")
    list_filter = ("recorded_at",)
    search_fields = ("tracking__order__id",)
    raw_id_fields = ("tracking",)
    readonly_fields = ("display_coords",)
    exclude = ("location",)

    @admin.display(description="Coordenadas (lat, lon)")
    def display_coords(self, obj: TrackingPoint) -> str:
        if obj.location is None:
            return "—"
        return f"{obj.location.y:.6f}, {obj.location.x:.6f}"
