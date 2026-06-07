"""URLs públicas de archivos en MEDIA."""

from django.conf import settings


def build_public_media_url(relative_url: str) -> str:
    if not relative_url:
        return ""

    if relative_url.startswith(("http://", "https://")):
        return relative_url

    base = getattr(settings, "MEDIA_PUBLIC_BASE_URL", "")
    if not base:
        return relative_url

    return f"{base.rstrip('/')}/{relative_url.lstrip('/')}"
