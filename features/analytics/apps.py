from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.analytics"
    label = "analytics"

    def ready(self) -> None:
        import features.analytics.infrastructure.admin  # noqa: F401

