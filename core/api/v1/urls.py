"""Router central de la API versión 1."""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("accounts/", include("features.accounts.infrastructure.urls")),
    path("stores/", include("features.stores.infrastructure.urls")),
    path("stores/", include("features.products.infrastructure.urls")),
    path("orders/", include("features.orders.infrastructure.urls")),
    path("orders/", include("features.delivery.infrastructure.urls")),
    path("orders/", include("features.chat.infrastructure.urls")),
    path("delivery/", include("features.delivery.infrastructure.offer_urls")),
    path("analytics/", include("features.analytics.infrastructure.urls")),
    path("marketing/", include("features.marketing.infrastructure.urls")),
    path("cart/", include("features.cart.infrastructure.urls")),
    path("", include("features.payments.infrastructure.urls")),
]
