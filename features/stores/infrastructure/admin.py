from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from features.stores.infrastructure.models import Store


@admin.register(Store)
class StoreAdmin(GISModelAdmin):
    list_display = ("name", "owner", "status", "address", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "owner__username", "address")
    raw_id_fields = ("owner",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": 12,
            "default_lat": 4.711,
            "default_lon": -74.072,
        },
    }
