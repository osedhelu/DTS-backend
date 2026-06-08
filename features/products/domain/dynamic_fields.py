"""Validación de parámetros dinámicos por categoría (configuracion_campos / valores_dinamicos)."""

from __future__ import annotations

from typing import Any

from features.products.domain.exceptions import InvalidDynamicFieldError

FREE_TEXT = "texto_libre"


def validate_field_config(raw: Any) -> dict[str, list[str] | str]:
    if raw in (None, {}):
        return {}

    if not isinstance(raw, dict):
        raise InvalidDynamicFieldError("configuracion_campos debe ser un objeto JSON")

    normalized: dict[str, list[str] | str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            raise InvalidDynamicFieldError("Cada parámetro debe tener un nombre válido")
        field_key = key.strip()

        if isinstance(value, list):
            options = [str(option).strip() for option in value if str(option).strip()]
            if not options:
                raise InvalidDynamicFieldError(
                    f"El parámetro '{field_key}' debe tener al menos una opción"
                )
            normalized[field_key] = options
            continue

        if value == FREE_TEXT:
            normalized[field_key] = FREE_TEXT
            continue

        raise InvalidDynamicFieldError(
            f"El parámetro '{field_key}' debe ser una lista de opciones o '{FREE_TEXT}'"
        )

    return normalized


def resolve_field_config(
    category_config: dict[str, list[str] | str] | None,
    subcategory_config: dict[str, list[str] | str] | None,
) -> dict[str, list[str] | str]:
    subcategory_config = subcategory_config or {}
    if subcategory_config:
        return subcategory_config
    return category_config or {}


def validate_dynamic_values(
    field_config: dict[str, list[str] | str],
    raw_values: Any,
) -> dict[str, str]:
    if not field_config:
        return {}

    if raw_values in (None, {}):
        raise InvalidDynamicFieldError("Faltan valores para los parámetros de la categoría")

    if not isinstance(raw_values, dict):
        raise InvalidDynamicFieldError("valores_dinamicos debe ser un objeto JSON")

    extra_keys = set(raw_values) - set(field_config)
    if extra_keys:
        names = ", ".join(sorted(extra_keys))
        raise InvalidDynamicFieldError(f"Parámetros no permitidos: {names}")

    normalized: dict[str, str] = {}
    for key, rule in field_config.items():
        if key not in raw_values:
            raise InvalidDynamicFieldError(f"Falta el parámetro '{key}'")

        value = raw_values[key]
        if rule == FREE_TEXT:
            if not isinstance(value, str) or not value.strip():
                raise InvalidDynamicFieldError(
                    f"El parámetro '{key}' requiere un texto"
                )
            normalized[key] = value.strip()
            continue

        if not isinstance(value, str) or value not in rule:
            allowed = ", ".join(rule)
            raise InvalidDynamicFieldError(
                f"Valor inválido para '{key}'. Opciones: {allowed}"
            )
        normalized[key] = value

    return normalized
