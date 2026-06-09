"""Validación de parámetros dinámicos por categoría (field_config / dynamic_values)."""

from __future__ import annotations

from typing import Any, Literal

from features.products.domain.exceptions import InvalidDynamicFieldError

FREE_TEXT = "texto_libre"
MULTI = "multi"
SINGLE = "single"

FieldMode = Literal["multi", "single", "free_text"]
FieldRule = dict[str, Any] | list[str] | str


def _dedupe_options(options: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for option in options:
        cleaned = option.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def parse_field_rule(value: Any) -> tuple[FieldMode, list[str] | None]:
    if value == FREE_TEXT:
        return "free_text", None

    if isinstance(value, list):
        options = _dedupe_options([str(option) for option in value])
        if not options:
            raise InvalidDynamicFieldError("Cada lista de opciones debe tener al menos un valor")
        return MULTI, options

    if isinstance(value, dict):
        mode = value.get("mode", MULTI)
        if mode not in (MULTI, SINGLE):
            raise InvalidDynamicFieldError("mode debe ser 'multi' o 'single'")
        raw_options = value.get("options")
        if not isinstance(raw_options, list):
            raise InvalidDynamicFieldError("options debe ser una lista")
        options = _dedupe_options([str(option) for option in raw_options])
        if not options:
            raise InvalidDynamicFieldError("Cada lista de opciones debe tener al menos un valor")
        return mode, options

    raise InvalidDynamicFieldError(
        f"Regla inválida: debe ser '{FREE_TEXT}', una lista o {{mode, options}}"
    )


def normalize_field_rule(value: Any) -> FieldRule:
    mode, options = parse_field_rule(value)
    if mode == "free_text":
        return FREE_TEXT
    return {"mode": mode, "options": options}


def get_field_options(rule: FieldRule) -> list[str] | None:
    mode, options = parse_field_rule(rule)
    return options


def get_field_mode(rule: FieldRule) -> FieldMode:
    mode, _ = parse_field_rule(rule)
    return mode


def validate_field_config(raw: Any) -> dict[str, FieldRule]:
    if raw in (None, {}):
        return {}

    if not isinstance(raw, dict):
        raise InvalidDynamicFieldError("field_config debe ser un objeto JSON")

    normalized: dict[str, FieldRule] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            raise InvalidDynamicFieldError("Cada parámetro debe tener un nombre válido")
        normalized[key.strip()] = normalize_field_rule(value)

    return normalized


def resolve_field_config(
    category_config: dict[str, FieldRule] | None,
    subcategory_config: dict[str, FieldRule] | None,
) -> dict[str, FieldRule]:
    """Combina categoría padre + subcategoría (la hija hereda y puede sobrescribir)."""
    merged: dict[str, FieldRule] = dict(category_config or {})
    merged.update(subcategory_config or {})
    return merged


def validate_dynamic_values(
    field_config: dict[str, FieldRule],
    raw_values: Any,
) -> dict[str, str | list[str] | dict[str, Any]]:
    if not field_config:
        return {}

    if raw_values in (None, {}):
        raise InvalidDynamicFieldError("Faltan valores para los parámetros de la categoría")

    if not isinstance(raw_values, dict):
        raise InvalidDynamicFieldError("dynamic_values debe ser un objeto JSON")

    extra_keys = set(raw_values) - set(field_config)
    if extra_keys:
        names = ", ".join(sorted(extra_keys))
        raise InvalidDynamicFieldError(f"Parámetros no permitidos: {names}")

    normalized: dict[str, str | list[str] | dict[str, Any]] = {}
    for key, rule in field_config.items():
        if key not in raw_values:
            raise InvalidDynamicFieldError(f"Falta el parámetro '{key}'")

        value = raw_values[key]
        mode = get_field_mode(rule)
        options = get_field_options(rule)

        if mode == "free_text":
            if not isinstance(value, str) or not value.strip():
                raise InvalidDynamicFieldError(f"El parámetro '{key}' requiere un texto")
            normalized[key] = value.strip()
            continue

        if mode == SINGLE:
            if isinstance(value, dict):
                raise InvalidDynamicFieldError(
                    f"El parámetro '{key}' no admite precios por opción"
                )
            if isinstance(value, list):
                if len(value) != 1:
                    raise InvalidDynamicFieldError(
                        f"El parámetro '{key}' admite una sola opción"
                    )
                value = value[0]
            if not isinstance(value, str) or value not in (options or []):
                allowed = ", ".join(options or [])
                raise InvalidDynamicFieldError(
                    f"Valor inválido para '{key}'. Opciones: {allowed}"
                )
            normalized[key] = value
            continue

        selected = extract_multi_options(value)
        if not selected:
            raise InvalidDynamicFieldError(
                f"El parámetro '{key}' requiere al menos una opción seleccionada"
            )

        seen: set[str] = set()
        cleaned_selected: list[str] = []
        for option in selected:
            if option not in (options or []):
                allowed = ", ".join(options or [])
                raise InvalidDynamicFieldError(
                    f"Opción '{option}' no permitida en '{key}'. Disponibles: {allowed}"
                )
            if option not in seen:
                seen.add(option)
                cleaned_selected.append(option)

        prices = extract_option_prices(value)
        for option in prices:
            if option not in cleaned_selected:
                raise InvalidDynamicFieldError(
                    f"Precio definido para '{option}' pero no está seleccionado en '{key}'"
                )

        if prices:
            normalized[key] = {"options": cleaned_selected, "prices": prices}
        else:
            normalized[key] = cleaned_selected

    return normalized


def extract_multi_options(value: str | list[str] | dict[str, Any]) -> list[str]:
    if isinstance(value, dict):
        raw_options = value.get("options", [])
        if not isinstance(raw_options, list):
            raise InvalidDynamicFieldError("options debe ser una lista")
        return [str(option).strip() for option in raw_options if str(option).strip()]

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if isinstance(value, list):
        return [str(option).strip() for option in value if str(option).strip()]

    raise InvalidDynamicFieldError("Formato inválido para parámetro multi")


def extract_option_prices(value: str | list[str] | dict[str, Any]) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    raw_prices = value.get("prices")
    if raw_prices in (None, {}):
        return {}

    if not isinstance(raw_prices, dict):
        raise InvalidDynamicFieldError("prices debe ser un objeto JSON")

    normalized: dict[str, str] = {}
    for option, price in raw_prices.items():
        if not isinstance(option, str) or not option.strip():
            raise InvalidDynamicFieldError("Cada precio debe tener una opción válida")
        if price in (None, ""):
            continue
        normalized[option.strip()] = str(price).strip()

    return normalized

