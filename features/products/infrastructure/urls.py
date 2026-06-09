from django.urls import path

from features.products.infrastructure.category_image_views import (
    CategoryImageDetailView,
    CategoryImageUploadView,
)
from features.products.infrastructure.product_catalog_views import (
    ProductImageDetailView,
    ProductImageUploadView,
    ProductIngredientListView,
    ProductVariantListView,
)
from features.products.infrastructure.views import (
    StoreCategoryDetailView,
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
        "<int:store_id>/products/<int:product_id>/variants/",
        ProductVariantListView.as_view(),
        name="store-product-variants",
    ),
    path(
        "<int:store_id>/products/<int:product_id>/ingredients/",
        ProductIngredientListView.as_view(),
        name="store-product-ingredients",
    ),
    path(
        "<int:store_id>/products/<int:product_id>/images/",
        ProductImageUploadView.as_view(),
        name="store-product-images",
    ),
    path(
        "<int:store_id>/products/<int:product_id>/images/<int:image_id>/",
        ProductImageDetailView.as_view(),
        name="store-product-image-detail",
    ),
    path(
        "<int:store_id>/categories/",
        StoreCategoryListCreateView.as_view(),
        name="store-categories-list-create",
    ),
    path(
        "<int:store_id>/categories/<int:category_id>/",
        StoreCategoryDetailView.as_view(),
        name="store-categories-detail",
    ),
    path(
        "<int:store_id>/categories/<int:category_id>/images/",
        CategoryImageUploadView.as_view(),
        name="store-category-images",
    ),
    path(
        "<int:store_id>/categories/<int:category_id>/images/<int:image_id>/",
        CategoryImageDetailView.as_view(),
        name="store-category-image-detail",
    ),
]
