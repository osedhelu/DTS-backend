from django.contrib import admin

from features.orders.infrastructure.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "unit_price", "quantity", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "store", "driver", "status", "order_type", "total", "created_at")
    list_filter = ("status", "order_type", "store")
    search_fields = ("customer__username", "store__name", "driver__username")
    raw_id_fields = ("customer", "store", "driver")
    inlines = (OrderItemInline,)
    readonly_fields = ("created_at", "updated_at")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "quantity", "unit_price")
    search_fields = ("product_name",)
    raw_id_fields = ("order", "product")
