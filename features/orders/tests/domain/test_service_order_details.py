from datetime import datetime, timezone

import pytest

from features.orders.domain.exceptions import InvalidServiceOrderDetailsError
from features.orders.domain.value_objects import OrderType, ServiceOrderDetails


def test_service_order_details_validation():
    details = ServiceOrderDetails(
        service_address="Calle 100 #15-20, Bogotá",
        customer_notes="Timbre roto, llamar al llegar",
        scheduled_at=datetime(2026, 6, 10, 14, 0, tzinfo=timezone.utc),
        latitude=4.7110,
        longitude=-74.0721,
        duration_minutes=180,
    )

    assert details.service_address == "Calle 100 #15-20, Bogotá"
    assert details.customer_notes == "Timbre roto, llamar al llegar"
    assert details.duration_minutes == 180
    assert OrderType.SERVICE == "service"
    assert OrderType.DELIVERY == "delivery"

    minimal = ServiceOrderDetails(service_address="Carrera 7 #45-10")
    assert minimal.latitude is None
    assert minimal.scheduled_at is None

    with pytest.raises(InvalidServiceOrderDetailsError, match="dirección"):
        ServiceOrderDetails(service_address="   ")

    with pytest.raises(InvalidServiceOrderDetailsError, match="latitud y longitud"):
        ServiceOrderDetails(service_address="Calle 1", latitude=4.71)

    with pytest.raises(InvalidServiceOrderDetailsError, match="Latitud inválida"):
        ServiceOrderDetails(
            service_address="Calle 1",
            latitude=999.0,
            longitude=-74.0,
        )

    with pytest.raises(InvalidServiceOrderDetailsError, match="duración"):
        ServiceOrderDetails(service_address="Calle 1", duration_minutes=0)
