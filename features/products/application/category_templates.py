from dataclasses import dataclass

from features.stores.domain.entities import StoreVertical

CATEGORY_TEMPLATES: dict[StoreVertical, dict[str, list[str]]] = {
    StoreVertical.FOOD: {
        "Comida rápida": ["Hamburguesas", "Perros calientes", "Alitas"],
        "Restaurante": ["Entradas", "Platos fuertes", "Bebidas"],
    },
    StoreVertical.SERVICES: {
        "Servicios del hogar": ["Plomería", "Electricidad", "Limpieza"],
        "Servicios personales": ["Peluquería", "Masajes", "Manicure"],
    },
    StoreVertical.RETAIL: {
        "Productos hogar": ["Cocina", "Decoración", "Organización"],
        "Electrónica": ["Accesorios", "Audio", "Computación"],
    },
}


@dataclass(frozen=True)
class CategoryTemplateDefinition:
    name: str
    subcategories: list[str]


class CategoryTemplateNotFoundError(ValueError):
    pass


class CategoryTemplateAlreadyImportedError(ValueError):
    pass


def get_template_names(vertical: StoreVertical) -> list[str]:
    return list(CATEGORY_TEMPLATES.get(vertical, {}).keys())


def get_template_definition(
    vertical: StoreVertical,
    template_name: str,
) -> CategoryTemplateDefinition:
    templates = CATEGORY_TEMPLATES.get(vertical, {})
    subcategories = templates.get(template_name)
    if subcategories is None:
        available = ", ".join(templates.keys()) or "ninguna"
        raise CategoryTemplateNotFoundError(
            f"Plantilla '{template_name}' no válida para vertical {vertical.value}. "
            f"Opciones: {available}"
        )
    return CategoryTemplateDefinition(name=template_name, subcategories=list(subcategories))


def _matches_template_query(query: str, template_name: str, subcategories: list[str]) -> bool:
    if not query.strip():
        return True
    q = query.strip().casefold()
    if q in template_name.casefold():
        return True
    return any(q in sub.casefold() for sub in subcategories)


def list_category_templates(
    vertical: StoreVertical,
    *,
    query: str = "",
    imported_root_names: set[str] | None = None,
) -> list[dict]:
    imported = {name.casefold() for name in (imported_root_names or set())}
    results: list[dict] = []

    for template_name, subcategories in CATEGORY_TEMPLATES.get(vertical, {}).items():
        if not _matches_template_query(query, template_name, subcategories):
            continue

        results.append(
            {
                "name": template_name,
                "subcategories": list(subcategories),
                "already_imported": template_name.casefold() in imported,
            }
        )

    return results


def import_store_category_template(
    store_id: int,
    vertical: StoreVertical,
    template_name: str,
) -> dict:
    """Copia plantilla DTS a la tienda (raíz + subcategorías)."""
    from features.products.infrastructure.models import Category

    definition = get_template_definition(vertical, template_name.strip())

    if Category.objects.filter(
        store_id=store_id,
        parent__isnull=True,
        name__iexact=definition.name,
    ).exists():
        raise CategoryTemplateAlreadyImportedError(
            f"La plantilla «{definition.name}» ya está en tu tienda"
        )

    parent = Category.objects.create(
        store_id=store_id,
        name=definition.name,
        parent=None,
    )
    created = 1
    for name in definition.subcategories:
        Category.objects.create(store_id=store_id, name=name, parent=parent)
        created += 1

    return {
        "template_name": definition.name,
        "categories_created": created,
        "root_category_id": parent.id,
    }


def seed_store_categories(store_id: int, vertical: StoreVertical, template_name: str) -> int:
    """Usado en onboarding — misma lógica que importación manual."""
    try:
        result = import_store_category_template(store_id, vertical, template_name)
    except CategoryTemplateNotFoundError as exc:
        from features.accounts.domain.exceptions import InvalidCategoryTemplateError

        raise InvalidCategoryTemplateError(str(exc)) from exc
    return int(result["categories_created"])
