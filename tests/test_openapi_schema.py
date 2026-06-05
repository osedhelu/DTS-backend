import yaml
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status


EXPECTED_PATHS = (
    "/api/v1/accounts/register/",
    "/api/v1/accounts/login/",
    "/api/v1/stores/",
    "/api/v1/stores/{store_id}/products/",
    "/api/v1/orders/",
    "/api/v1/orders/{order_id}/tracking/",
)


def test_schema_generates(api_client):
    response = api_client.get(reverse("schema"))
    assert response.status_code == status.HTTP_200_OK

    schema = yaml.safe_load(response.content)
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "DTS Delivery API"
    assert schema["info"]["version"] == "1.0.0"
    assert "paths" in schema
    assert "components" in schema

    paths = schema["paths"]
    for expected_path in EXPECTED_PATHS:
        assert expected_path in paths, f"Falta la ruta documentada: {expected_path}"

    register_post = paths["/api/v1/accounts/register/"]["post"]
    assert register_post["tags"] == ["accounts"]
    assert "requestBody" in register_post
    assert "responses" in register_post

    tracking_get = paths["/api/v1/orders/{order_id}/tracking/"]["get"]
    assert tracking_get["tags"] == ["delivery"]


def test_schema_generator_produces_valid_document():
    schema = SchemaGenerator().get_schema(request=None, public=True)

    assert schema is not None
    assert schema["openapi"].startswith("3.")
    assert len(schema["paths"]) >= len(EXPECTED_PATHS)
