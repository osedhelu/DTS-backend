from features.stores.domain.entities import StoreVertical


def test_store_vertical_values():
    assert StoreVertical.FOOD.value == "FOOD"
    assert StoreVertical.SERVICES.value == "SERVICES"
    assert StoreVertical.RETAIL.value == "RETAIL"
    assert len(StoreVertical) == 3
