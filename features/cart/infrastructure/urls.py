from django.urls import path

from features.cart.infrastructure.views import CartDetailView, CartItemDetailView, CartItemsView

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),
    path("items/", CartItemsView.as_view(), name="cart-items"),
    path("items/<int:product_id>/", CartItemDetailView.as_view(), name="cart-item-detail"),
]
