from django.urls import include, path
from rest_framework.routers import DefaultRouter

from features.marketing.infrastructure.coupon_validate_view import ValidateCouponView
from features.marketing.infrastructure.views import (
    ActiveBannersView,
    BannerViewSet,
    CouponViewSet,
    FeaturedProductsView,
)

router = DefaultRouter()
router.register("coupons", CouponViewSet, basename="marketing-coupon")
router.register("banners", BannerViewSet, basename="marketing-banner")

urlpatterns = [
    path("coupons/validate/", ValidateCouponView.as_view(), name="marketing-validate-coupon"),
    path("banners/active/", ActiveBannersView.as_view(), name="marketing-active-banners"),
    path(
        "featured-products/",
        FeaturedProductsView.as_view(),
        name="marketing-featured-products",
    ),
    path("", include(router.urls)),
]
