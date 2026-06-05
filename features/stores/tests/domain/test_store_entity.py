from features.stores.domain.entities import Store, StoreStatus


def test_store_toggle_status():
    store = Store(name="Restaurante Central", owner_id=1, status=StoreStatus.CLOSED)

    assert store.is_open is False

    new_status = store.toggle_status()
    assert new_status == StoreStatus.OPEN
    assert store.is_open is True

    new_status = store.toggle_status()
    assert new_status == StoreStatus.CLOSED
    assert store.is_open is False


def test_store_open_and_close():
    store = Store(name="Café Norte", owner_id=2)

    assert store.status == StoreStatus.CLOSED

    store.open()
    assert store.status == StoreStatus.OPEN

    store.close()
    assert store.status == StoreStatus.CLOSED
