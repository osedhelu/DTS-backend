from unittest.mock import MagicMock

import pytest

from features.stores.application.dto import CreateStoreDTO, UpdateStoreStatusDTO
from features.stores.application.use_cases.create_store import CreateStoreUseCase
from features.stores.application.use_cases.update_store_status import UpdateStoreStatusUseCase
from features.stores.domain.entities import Store, StoreStatus
from features.stores.domain.exceptions import InvalidGeoLocationError, NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.value_objects import GeoLocation


def test_create_store_use_case():
    repository = MagicMock()
    created_store = Store(id=1, name="Restaurante Central", owner_id=10, status=StoreStatus.CLOSED)
    repository.create.return_value = created_store

    use_case = CreateStoreUseCase(repository)
    dto = CreateStoreDTO(
        owner_id=10,
        name="  Restaurante Central  ",
        latitude=4.7110,
        longitude=-74.0721,
        address="Calle 100 #15-20",
    )

    result = use_case.execute(dto)

    repository.create.assert_called_once_with(
        {
            "owner_id": 10,
            "name": "Restaurante Central",
            "latitude": 4.7110,
            "longitude": -74.0721,
            "address": "Calle 100 #15-20",
            "status": StoreStatus.CLOSED,
        }
    )
    assert result == created_store


def test_create_store_use_case_invalid_location():
    repository = MagicMock()
    use_case = CreateStoreUseCase(repository)

    dto = CreateStoreDTO(
        owner_id=10,
        name="Restaurante",
        latitude=999.0,
        longitude=-74.0721,
    )

    with pytest.raises(InvalidGeoLocationError):
        use_case.execute(dto)

    repository.create.assert_not_called()


def test_close_store():
    repository = MagicMock()
    existing_store = Store(id=5, name="Café Norte", owner_id=10, status=StoreStatus.OPEN)
    closed_store = Store(id=5, name="Café Norte", owner_id=10, status=StoreStatus.CLOSED)

    repository.get_by_id.return_value = existing_store
    repository.update_status.return_value = closed_store

    use_case = UpdateStoreStatusUseCase(repository)
    result = use_case.close(store_id=5, owner_id=10)

    repository.get_by_id.assert_called_once_with(5)
    repository.update_status.assert_called_once_with(5, StoreStatus.CLOSED)
    assert result.status == StoreStatus.CLOSED


def test_close_store_not_found():
    repository = MagicMock()
    repository.get_by_id.return_value = None

    use_case = UpdateStoreStatusUseCase(repository)

    with pytest.raises(StoreNotFoundError):
        use_case.close(store_id=99, owner_id=10)


def test_close_store_not_owner():
    repository = MagicMock()
    repository.get_by_id.return_value = Store(id=5, name="Café Norte", owner_id=10, status=StoreStatus.OPEN)

    use_case = UpdateStoreStatusUseCase(repository)

    with pytest.raises(NotStoreOwnerError):
        use_case.close(store_id=5, owner_id=999)

    repository.update_status.assert_not_called()
