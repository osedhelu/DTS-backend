import importlib
from pathlib import Path

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:
        features_dir = Path(__file__).resolve().parent.parent / "features"
        for app_dir in sorted(features_dir.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith("_"):
                continue
            if not (app_dir / "infrastructure" / "admin.py").exists():
                continue
            importlib.import_module(f"features.{app_dir.name}.infrastructure.admin")
