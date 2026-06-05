"""Registro dinámico de Django apps — T1.1.3."""
from pathlib import Path


def _app_config_path(module_name: str) -> str:
    class_name = "".join(part.capitalize() for part in module_name.split("_")) + "Config"
    return f"features.{module_name}.apps.{class_name}"


def discover_django_apps(base_dir: Path) -> list[str]:
    """Descubre AppConfig explícito en features/ (garantiza hooks ready())."""
    apps: list[str] = []

    for package_root, _prefix in ((base_dir / "features", "features"),):
        if not package_root.is_dir():
            continue
        for app_dir in sorted(package_root.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith("_"):
                continue
            if (app_dir / "apps.py").exists():
                apps.append(_app_config_path(app_dir.name))

    return apps


def build_installed_apps(base_dir: Path) -> list[str]:
    core_apps = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.gis",
        "rest_framework",
        "corsheaders",
        "drf_spectacular",
    ]
    # CoreConfig al final: carga admin.py de cada feature tras registrar modelos
    return core_apps + discover_django_apps(base_dir) + ["core.apps.CoreConfig"]
