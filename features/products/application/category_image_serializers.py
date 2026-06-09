"""Serialización de imágenes de categoría para API."""

from core.media_urls import build_public_media_url
from features.products.domain.entities import CategoryImage


def serialize_category_image(image: CategoryImage) -> dict:
    return {
        "id": image.id,
        "url": build_public_media_url(image.image_path),
        "is_primary": image.is_primary,
    }


def serialize_category_images(images: list[CategoryImage]) -> tuple[list[dict], str | None]:
    payload = [serialize_category_image(image) for image in images]
    primary_url = next((item["url"] for item in payload if item["is_primary"]), None)
    if primary_url is None and payload:
        primary_url = payload[0]["url"]
    return payload, primary_url
