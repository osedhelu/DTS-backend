from django.urls import path

from features.products.infrastructure.views import (
    StoreCategoryListCreateView,
    StoreProductDetailView,
    StoreProductListCreateView,
)

urlpatterns = [
    path(
        "<int:store_id>/products/",
        StoreProductListCreateView.as_view(),
        name="store-products-list-create",
    ),
    path(
        "<int:store_id>/products/<int:product_id>/",
        StoreProductDetailView.as_view(),
        name="store-products-detail",
    ),
    path(
        "<int:store_id>/categories/",
        StoreCategoryListCreateView.as_view(),
        name="store-categories-list-create",
    ),
]
