import pytest

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import (
    CustomerProfile,
    CustomUser,
    DriverProfile,
    MerchantProfile,
)


@pytest.mark.django_db
def test_profile_creation():
    merchant_user = CustomUser.objects.create_user(
        username="merchant_shop",
        email="shop@test.com",
        password="pass123",
        role=UserRole.MERCHANT,
    )
    merchant_profile = MerchantProfile.objects.create(
        user=merchant_user,
        business_name="Restaurante El Buen Sabor",
        tax_id="900123456",
        phone="+573001112233",
        address="Calle 10 #20-30",
    )
    assert merchant_profile.user == merchant_user
    assert merchant_user.merchant_profile.business_name == "Restaurante El Buen Sabor"

    driver_user = CustomUser.objects.create_user(
        username="driver_juan",
        email="driver@test.com",
        password="pass123",
        role=UserRole.DRIVER,
    )
    driver_profile = DriverProfile.objects.create(
        user=driver_user,
        phone="+573004445566",
        license_number="LIC-12345",
        vehicle_type="moto",
        is_online=True,
    )
    assert driver_profile.user == driver_user
    assert driver_user.driver_profile.is_online is True

    customer_user = CustomUser.objects.create_user(
        username="customer_ana",
        email="customer@test.com",
        password="pass123",
        role=UserRole.CUSTOMER,
    )
    customer_profile = CustomerProfile.objects.create(
        user=customer_user,
        phone="+573007778899",
        default_address="Carrera 7 #45-67",
    )
    assert customer_profile.user == customer_user
    assert customer_user.customer_profile.default_address == "Carrera 7 #45-67"
