from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from features.accounts.infrastructure.models import (
    CustomerProfile,
    CustomUser,
    DeviceToken,
    DriverProfile,
    MerchantProfile,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)
    fieldsets = UserAdmin.fieldsets + (
        ("Rol DTS", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Rol DTS", {"fields": ("role",)}),
    )


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "phone", "tax_id")
    search_fields = ("business_name", "user__username", "user__email")


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "is_online", "vehicle_type")
    list_filter = ("is_online", "vehicle_type")
    search_fields = ("user__username", "user__email", "license_number")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "user__email")


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "updated_at")
    list_filter = ("platform", "is_active")
    search_fields = ("user__username", "token")
