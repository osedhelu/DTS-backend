from django.urls import include, path
from rest_framework.routers import DefaultRouter

from features.marketing.infrastructure.views import ActiveBannersView, CouponViewSet

router = DefaultRouter()
router.register("coupons", CouponViewSet, basename="marketing-coupon")

urlpatterns = [
    path("banners/active/", ActiveBannersView.as_view(), name="marketing-active-banners"),
    path("", include(router.urls)),
]
