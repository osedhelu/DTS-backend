from django.urls import path

from features.stores.infrastructure.views import StoreDetailView, StoreListCreateView

urlpatterns = [
    path("", StoreListCreateView.as_view(), name="stores-list-create"),
    path("<int:store_id>/", StoreDetailView.as_view(), name="stores-detail"),
]
