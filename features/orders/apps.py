from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.orders"
    label = "orders"

    def ready(self):
        import features.orders.infrastructure.signals  # noqa: F401

