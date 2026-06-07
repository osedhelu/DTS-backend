from features.products.application.category_templates import (
    CATEGORY_TEMPLATES,
    get_template_names,
)
from features.stores.domain.entities import StoreVertical


def test_category_templates_by_vertical():
    food_templates = get_template_names(StoreVertical.FOOD)
    assert "Comida rápida" in food_templates
    assert "Hamburguesas" in CATEGORY_TEMPLATES[StoreVertical.FOOD]["Comida rápida"]

    services_templates = get_template_names(StoreVertical.SERVICES)
    assert "Servicios del hogar" in services_templates
    assert "Limpieza" in CATEGORY_TEMPLATES[StoreVertical.SERVICES]["Servicios del hogar"]

    retail_templates = get_template_names(StoreVertical.RETAIL)
    assert "Electrónica" in retail_templates
    assert "Audio" in CATEGORY_TEMPLATES[StoreVertical.RETAIL]["Electrónica"]
