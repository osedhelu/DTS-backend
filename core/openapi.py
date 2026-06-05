"""Hooks y utilidades para la generación del esquema OpenAPI."""

from rest_framework import serializers
from drf_spectacular.utils import inline_serializer

API_TAGS = [
    {"name": "accounts", "description": "Registro, autenticación JWT y tokens FCM"},
    {"name": "stores", "description": "Comercios y ubicación"},
    {"name": "products", "description": "Catálogo, categorías y servicios"},
    {"name": "orders", "description": "Pedidos delivery y servicios a domicilio"},
    {"name": "delivery", "description": "Tracking GPS del conductor"},
    {"name": "schema", "description": "Documentación OpenAPI"},
]

DetailErrorSerializer = inline_serializer(
    name="DetailError",
    fields={"detail": serializers.CharField()},
)


def _tag_for_path(path: str) -> str:
    if path.startswith("/api/v1/accounts/"):
        return "accounts"
    if "/tracking/" in path:
        return "delivery"
    if path.startswith("/api/v1/orders/"):
        return "orders"
    if "/products/" in path or "/categories/" in path:
        return "products"
    if path.startswith("/api/v1/stores/"):
        return "stores"
    if path.startswith("/api/v1/schema/"):
        return "schema"
    return "api"


def assign_path_tags(result, generator, request, public):
    """Asigna tags por prefijo de ruta en el esquema generado."""
    for path, path_item in result.get("paths", {}).items():
        tag = _tag_for_path(path)
        for method, operation in path_item.items():
            if method in {"get", "post", "put", "patch", "delete", "head", "options"}:
                operation["tags"] = [tag]
    return result
