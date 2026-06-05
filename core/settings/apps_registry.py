"""Registro dinámico de Django apps — T1.1.3."""
from pathlib import Path


def discover_django_apps(base_dir: Path) -> list[str]:
    """Descubre apps en features/ que tengan apps.py."""
    apps: list[str] = []

    for package_root, prefix in ((base_dir / "features", "features"),):
        if not package_root.is_dir():
            continue
        for app_dir in sorted(package_root.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith("_"):
                continue
            if (app_dir / "apps.py").exists():
                apps.append(f"{prefix}.{app_dir.name}")

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
    return core_apps + discover_django_apps(base_dir)
