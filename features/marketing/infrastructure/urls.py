from django.urls import include, path
from rest_framework.routers import DefaultRouter

from features.marketing.infrastructure.views import (
    ActiveBannersView,
    BannerViewSet,
    CouponViewSet,
)

router = DefaultRouter()
router.register("coupons", CouponViewSet, basename="marketing-coupon")
router.register("banners", BannerViewSet, basename="marketing-banner")

urlpatterns = [
    path("banners/active/", ActiveBannersView.as_view(), name="marketing-active-banners"),
    path("", include(router.urls)),
]
