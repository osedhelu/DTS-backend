"""Unit tests for merchant order enrichment (sin PostGIS/GDAL)."""

from datetime import datetime, timezone
from types import SimpleNamespace

from features.orders.infrastructure.serializers import build_merchant_order_enrichment


def test_build_merchant_order_enrichment_with_customer_and_driver():
    customer_profile = SimpleNamespace(
        display_full_name=lambda: "Ana Cliente",
        phone="+573001112233",
    )
    customer = SimpleNamespace(
        customer_profile=customer_profile,
        get_full_name=lambda: "",
        username="customer1",
    )
    driver_profile = SimpleNamespace(full_name="Carlos Conductor", phone="+573009998877")
    driver = SimpleNamespace(
        username="driver1",
        driver_profile=driver_profile,
    )
    store = SimpleNamespace(address="Fallback store", latitude=4.0, longitude=-74.0)
    order = SimpleNamespace(
        store=store,
        customer=customer,
        driver_id=42,
        driver=driver,
        service_address="Calle 100 # 10-20",
        service_latitude=4.72,
        service_longitude=-74.05,
        customer_notes="Timbre rojo",
        created_at=datetime(2026, 7, 20, 15, 0, tzinfo=timezone.utc),
    )

    data = build_merchant_order_enrichment(order)

    assert data["customer_name"] == "Ana Cliente"
    assert data["customer_phone"] == "+573001112233"
    assert data["driver_name"] == "Carlos Conductor"
    assert data["driver_phone"] == "+573009998877"
    assert data["delivery_address"] == "Calle 100 # 10-20"
    assert data["service_address"] == "Calle 100 # 10-20"
    assert data["customer_notes"] == "Timbre rojo"
    assert data["created_at"] == "2026-07-20T15:00:00+00:00"


def test_build_merchant_order_enrichment_without_driver_falls_back_to_store():
    customer = SimpleNamespace(
        customer_profile=None,
        get_full_name=lambda: "Luis Pérez",
        username="luis",
    )
    store = SimpleNamespace(address="Calle Store 1", latitude=4.1, longitude=-74.1)
    order = SimpleNamespace(
        store=store,
        customer=customer,
        driver_id=None,
        driver=None,
        service_address="",
        service_latitude=None,
        service_longitude=None,
        customer_notes="  ",
        created_at=None,
    )

    data = build_merchant_order_enrichment(order)

    assert data["customer_name"] == "Luis Pérez"
    assert data["customer_phone"] is None
    assert data["driver_name"] is None
    assert data["delivery_address"] == "Calle Store 1"
    assert data["delivery_latitude"] == 4.1
    assert data["delivery_longitude"] == -74.1
    assert data["customer_notes"] is None
    assert data["created_at"] is None
