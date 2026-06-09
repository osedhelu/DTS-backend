from features.products.application.category_templates import (
    CATEGORY_TEMPLATES,
    get_template_names,
    list_category_templates,
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


def test_list_category_templates_filters_by_query():
    all_templates = list_category_templates(StoreVertical.FOOD)
    assert len(all_templates) == 2

    filtered = list_category_templates(StoreVertical.FOOD, query="entrada")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Restaurante"


def test_list_category_templates_marks_already_imported():
    templates = list_category_templates(
        StoreVertical.FOOD,
        imported_root_names={"Restaurante"},
    )
    restaurante = next(item for item in templates if item["name"] == "Restaurante")
    assert restaurante["already_imported"] is True

    comida = next(item for item in templates if item["name"] == "Comida rápida")
    assert comida["already_imported"] is False
