from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/v1/accounts/", include("features.accounts.infrastructure.urls")),
    path("api/v1/stores/", include("features.stores.infrastructure.urls")),
    # Portales web — activar en Fase 3
    # path("merchant/", include("portals.merchant.urls")),
    # path("admin-portal/", include("portals.admin_portal.urls")),
]
