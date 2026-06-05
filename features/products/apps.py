from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.products"
    label = "products"

    def ready(self) -> None:
        import features.products.infrastructure.admin  # noqa: F401

