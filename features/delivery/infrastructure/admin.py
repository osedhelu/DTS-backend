from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from features.delivery.infrastructure.models import DeliveryTracking, TrackingPoint


class TrackingPointInline(admin.TabularInline):
    model = TrackingPoint
    extra = 0
    readonly_fields = ("sequence", "recorded_at")


@admin.register(DeliveryTracking)
class DeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = ("order", "created_at", "updated_at")
    search_fields = ("order__id",)
    raw_id_fields = ("order",)
    inlines = (TrackingPointInline,)


@admin.register(TrackingPoint)
class TrackingPointAdmin(GISModelAdmin):
    list_display = ("tracking", "sequence", "recorded_at")
    raw_id_fields = ("tracking",)
