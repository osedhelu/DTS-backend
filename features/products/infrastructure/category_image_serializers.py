import os

from rest_framework import serializers

ALLOWED_CATEGORY_IMAGE_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
MAX_CATEGORY_SVG_BYTES = 256 * 1024


def _validate_category_image_file(value):
    extension = os.path.splitext(value.name)[1].lower()
    if extension not in ALLOWED_CATEGORY_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_CATEGORY_IMAGE_EXTENSIONS))
        raise serializers.ValidationError(
            f"Formato no permitido. Usa: {allowed}",
        )

    if extension == ".svg":
        content = value.read()
        value.seek(0)
        if len(content) > MAX_CATEGORY_SVG_BYTES:
            raise serializers.ValidationError(
                "El SVG no puede superar 256 KB.",
            )
        snippet = content[:4096].lower()
        if b"<svg" not in snippet:
            raise serializers.ValidationError("El archivo SVG no es válido.")

    return value


class UploadCategoryImageSerializer(serializers.Serializer):
    image = serializers.FileField()
    is_primary = serializers.BooleanField(default=False, required=False)

    def validate_image(self, value):
        return _validate_category_image_file(value)


class UpdateCategoryImageSerializer(serializers.Serializer):
    image = serializers.FileField(required=False)
    is_primary = serializers.BooleanField(required=False)

    def validate_image(self, value):
        return _validate_category_image_file(value)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Indica is_primary o sube un nuevo archivo.",
            )
        return attrs
