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


def get_template_names(vertical: StoreVertical) -> list[str]:
    return list(CATEGORY_TEMPLATES.get(vertical, {}).keys())


def seed_store_categories(store_id: int, vertical: StoreVertical, template_name: str) -> int:
    """Crea categoría raíz + subcategorías. Retorna cantidad de categorías creadas."""
    from features.accounts.domain.exceptions import InvalidCategoryTemplateError
    from features.products.infrastructure.models import Category

    templates = CATEGORY_TEMPLATES.get(vertical, {})
    subcategories = templates.get(template_name)
    if subcategories is None:
        available = ", ".join(templates.keys()) or "ninguna"
        raise InvalidCategoryTemplateError(
            f"Plantilla '{template_name}' no válida para vertical {vertical.value}. "
            f"Opciones: {available}"
        )

    parent = Category.objects.create(store_id=store_id, name=template_name, parent=None)
    created = 1
    for name in subcategories:
        Category.objects.create(store_id=store_id, name=name, parent=parent)
        created += 1
    return created
