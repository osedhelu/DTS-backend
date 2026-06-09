import pytest

from features.products.domain.dynamic_fields import (
    FREE_TEXT,
    MULTI,
    resolve_field_config,
    validate_dynamic_values,
    validate_field_config,
)
from features.products.domain.exceptions import InvalidDynamicFieldError


def test_validate_field_config_multi_single_and_free_text():
    config = validate_field_config(
        {
            "talla": {"mode": "multi", "options": ["S", "M", "L", "XL"]},
            "masa": ["tradicional", "delgada"],
            "notas": FREE_TEXT,
        }
    )

    assert config["talla"] == {"mode": MULTI, "options": ["S", "M", "L", "XL"]}
    assert config["masa"] == {"mode": MULTI, "options": ["tradicional", "delgada"]}
    assert config["notas"] == FREE_TEXT


def test_validate_field_config_rejects_invalid_shape():
    with pytest.raises(InvalidDynamicFieldError):
        validate_field_config({"talla": []})


def test_resolve_field_config_merges_parent_and_subcategory():
    root = {"talla": {"mode": "multi", "options": ["XS", "S", "M", "L", "XL"]}}
    sub = {"color": {"mode": "multi", "options": ["rojo", "azul"]}}
    merged = resolve_field_config(root, sub)

    assert merged["talla"] == root["talla"]
    assert merged["color"] == sub["color"]


def test_resolve_field_config_subcategory_overrides_same_key():
    root = {"talla": {"mode": "multi", "options": ["S", "M", "L"]}}
    sub = {"talla": {"mode": "multi", "options": ["28", "30", "32"]}}
    merged = resolve_field_config(root, sub)

    assert merged["talla"] == sub["talla"]


def test_validate_dynamic_values_multi_select():
    config = {
        "talla": {"mode": "multi", "options": ["S", "M", "L", "XL"]},
        "masa": ["tradicional", "delgada"],
    }
    values = validate_dynamic_values(
        config,
        {"talla": ["S", "M", "L"], "masa": ["delgada"]},
    )
    assert values == {"talla": ["S", "M", "L"], "masa": ["delgada"]}


def test_validate_dynamic_values_single_select():
    config = {"borde": {"mode": "single", "options": ["queso", "sencillo"]}}
    values = validate_dynamic_values(config, {"borde": "queso"})
    assert values == {"borde": "queso"}


def test_validate_dynamic_values_rejects_unknown_option():
    config = {"talla": {"mode": "multi", "options": ["S", "M"]}}
    with pytest.raises(InvalidDynamicFieldError):
        validate_dynamic_values(config, {"talla": ["XL"]})


def test_validate_dynamic_values_requires_at_least_one_multi_option():
    config = {"talla": {"mode": "multi", "options": ["S", "M"]}}
    with pytest.raises(InvalidDynamicFieldError):
        validate_dynamic_values(config, {"talla": []})


def test_validate_dynamic_values_requires_free_text():
    config = {"color": FREE_TEXT}
    with pytest.raises(InvalidDynamicFieldError):
        validate_dynamic_values(config, {"color": "  "})


def test_validate_dynamic_values_multi_with_prices():
    config = {"talla": {"mode": "multi", "options": ["S", "M", "L", "XL"]}}
    values = validate_dynamic_values(
        config,
        {
            "talla": {
                "options": ["M", "XL"],
                "prices": {"M": "25000", "XL": "29990"},
            }
        },
    )
    assert values == {
        "talla": {
            "options": ["M", "XL"],
            "prices": {"M": "25000", "XL": "29990"},
        }
    }
