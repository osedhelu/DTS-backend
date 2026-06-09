from django.core.files.uploadedfile import SimpleUploadedFile

from features.products.infrastructure.category_image_serializers import (
    UploadCategoryImageSerializer,
)


def test_upload_category_image_accepts_svg():
    svg = SimpleUploadedFile(
        "bebidas.svg",
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/></svg>',
        content_type="image/svg+xml",
    )
    serializer = UploadCategoryImageSerializer(data={"image": svg, "is_primary": True})

    assert serializer.is_valid(), serializer.errors


def test_upload_category_image_rejects_invalid_svg():
    invalid = SimpleUploadedFile(
        "bad.svg",
        b"not an svg file",
        content_type="image/svg+xml",
    )
    serializer = UploadCategoryImageSerializer(data={"image": invalid})

    assert not serializer.is_valid()
    assert "image" in serializer.errors
