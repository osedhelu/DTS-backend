from django.urls import path

from features.delivery.infrastructure.views import (
    AcceptOfferView,
    DriverOffersListView,
    RejectOfferView,
)

urlpatterns = [
    path("offers/", DriverOffersListView.as_view(), name="delivery-offers-list"),
    path(
        "offers/<int:order_id>/accept/",
        AcceptOfferView.as_view(),
        name="delivery-offers-accept",
    ),
    path(
        "offers/<int:order_id>/reject/",
        RejectOfferView.as_view(),
        name="delivery-offers-reject",
    ),
]
