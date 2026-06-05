from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.api.v1.urls")),
    # Portales web — activar en Fase 3
    # path("merchant/", include("portals.merchant.urls")),
    # path("admin-portal/", include("portals.admin_portal.urls")),
]
