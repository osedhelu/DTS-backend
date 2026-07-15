from django.urls import path

from features.chat.infrastructure.views import OrderMessagesView

urlpatterns = [
    path(
        "<int:order_id>/messages/",
        OrderMessagesView.as_view(),
        name="order-messages",
    ),
]
