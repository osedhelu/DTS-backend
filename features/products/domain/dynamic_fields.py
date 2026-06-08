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
) -> dict[str, str | list[str]]:
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

    normalized: dict[str, str | list[str]] = {}
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

        # multi — el producto elige qué opciones de la categoría ofrece
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or not value:
            raise InvalidDynamicFieldError(
                f"El parámetro '{key}' requiere al menos una opción seleccionada"
            )

        selected: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                raise InvalidDynamicFieldError(f"Valor inválido en '{key}'")
            option = item.strip()
            if not option:
                continue
            if option not in (options or []):
                allowed = ", ".join(options or [])
                raise InvalidDynamicFieldError(
                    f"Opción '{option}' no permitida en '{key}'. Disponibles: {allowed}"
                )
            if option not in seen:
                seen.add(option)
                selected.append(option)

        if not selected:
            raise InvalidDynamicFieldError(
                f"El parámetro '{key}' requiere al menos una opción seleccionada"
            )
        normalized[key] = selected

    return normalized
