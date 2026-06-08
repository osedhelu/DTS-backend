import pytest

from features.products.domain.dynamic_fields import (
    FREE_TEXT,
    resolve_field_config,
    validate_dynamic_values,
    validate_field_config,
)
from features.products.domain.exceptions import InvalidDynamicFieldError


def test_validate_field_config_select_and_free_text():
    config = validate_field_config(
        {
            "masa": ["tradicional", "delgada"],
            "borde": ["queso", "sencillo"],
            "color": FREE_TEXT,
        }
    )

    assert config["masa"] == ["tradicional", "delgada"]
    assert config["color"] == FREE_TEXT


def test_validate_field_config_rejects_invalid_shape():
    with pytest.raises(InvalidDynamicFieldError):
        validate_field_config({"talla": []})


def test_resolve_field_config_prefers_subcategory():
    root = {"talla": ["S", "M"]}
    sub = {"color": ["rojo", "azul"]}
    assert resolve_field_config(root, sub) == sub


def test_validate_dynamic_values_success():
    config = {"masa": ["tradicional", "delgada"], "borde": ["queso"]}
    values = validate_dynamic_values(config, {"masa": "delgada", "borde": "queso"})
    assert values == {"masa": "delgada", "borde": "queso"}


def test_validate_dynamic_values_rejects_unknown_option():
    config = {"masa": ["tradicional", "delgada"]}
    with pytest.raises(InvalidDynamicFieldError):
        validate_dynamic_values(config, {"masa": "integral"})


def test_validate_dynamic_values_requires_free_text():
    config = {"color": FREE_TEXT}
    with pytest.raises(InvalidDynamicFieldError):
        validate_dynamic_values(config, {"color": "  "})
