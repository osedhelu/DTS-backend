"""Utilidades compartidas para previews de imágenes en Django Admin."""

from django.utils.html import format_html

from core.media_urls import build_public_media_url


def admin_image_preview(
    url: str | None,
    *,
    max_height: int = 80,
    max_width: int = 80,
    alt: str = "",
) -> str:
    if not url:
        return "—"

    public_url = build_public_media_url(url)
    return format_html(
        (
            '<img src="{}" alt="{}" '
            'style="max-height:{}px;max-width:{}px;object-fit:cover;'
            'border-radius:6px;border:1px solid #d4d4d8;" />'
        ),
        public_url,
        alt,
        max_height,
        max_width,
    )
