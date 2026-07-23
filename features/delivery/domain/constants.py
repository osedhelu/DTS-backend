"""Constantes de radios geo (conductor + cliente)."""

from __future__ import annotations

DEFAULT_RADIUS_KM = 5.0
MIN_RADIUS_KM = 1.0
MAX_RADIUS_KM = 500.0

RADIUS_PRESETS_KM: tuple[float, ...] = (
    1.0,
    2.0,
    5.0,
    10.0,
    20.0,
    35.0,
    40.0,
    60.0,
    80.0,
    100.0,
    250.0,
    500.0,
)

# Compat: callers antiguos
MAX_DRIVER_OFFER_DISTANCE_KM = DEFAULT_RADIUS_KM


def normalize_radius_km(value: float | int | str | None) -> float:
    """Valida y normaliza un radio en km (preset o rango min–max)."""
    if value is None:
        return DEFAULT_RADIUS_KM
    try:
        radius = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("radius_km debe ser un número") from exc
    if radius < MIN_RADIUS_KM or radius > MAX_RADIUS_KM:
        raise ValueError(
            f"radius_km debe estar entre {MIN_RADIUS_KM:g} y {MAX_RADIUS_KM:g}"
        )
    # Aceptar presets exactos o cualquier valor en rango
    return radius
