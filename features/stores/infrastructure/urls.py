from django.urls import path

from features.marketing.infrastructure.store_promotion_views import (
    StorePromotionDetailView,
    StorePromotionListCreateView,
)
from features.stores.infrastructure.admin_store_views import AdminStoreModerationView
from features.stores.infrastructure.store_profile_views import StoreProfileView
from features.stores.infrastructure.views import (
    MerchantDashboardView,
    MerchantStoreListView,
    StoreDetailView,
    StoreListCreateView,
)

urlpatterns = [
    path("", StoreListCreateView.as_view(), name="stores-list-create"),
    path("mine/", MerchantStoreListView.as_view(), name="stores-mine"),
    path("<int:store_id>/", StoreDetailView.as_view(), name="stores-detail"),
    path(
        "<int:store_id>/profile/",
        StoreProfileView.as_view(),
        name="stores-profile",
    ),
    path(
        "<int:store_id>/moderation/",
        AdminStoreModerationView.as_view(),
        name="stores-admin-moderation",
    ),
    path(
        "<int:store_id>/merchant-dashboard/",
        MerchantDashboardView.as_view(),
        name="stores-merchant-dashboard",
    ),
    path(
        "<int:store_id>/promotions/",
        StorePromotionListCreateView.as_view(),
        name="store-promotions-list-create",
    ),
    path(
        "<int:store_id>/promotions/<int:promotion_id>/",
        StorePromotionDetailView.as_view(),
        name="store-promotions-detail",
    ),
]
