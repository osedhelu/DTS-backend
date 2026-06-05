from django.apps import AppConfig


class StoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.stores"
    label = "stores"

    def ready(self) -> None:
        import features.stores.infrastructure.admin  # noqa: F401

