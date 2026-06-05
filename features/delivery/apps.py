from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.delivery"
    label = "delivery"

    def ready(self) -> None:
        import features.delivery.infrastructure.admin  # noqa: F401

