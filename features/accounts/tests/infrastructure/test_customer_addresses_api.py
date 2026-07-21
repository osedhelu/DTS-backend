import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, CustomerAddress, CustomerProfile


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _create_customer(username: str = "customer_addresses") -> CustomUser:
    user = CustomUser.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    CustomerProfile.objects.create(user=user, phone="+573001112233")
    return user


@pytest.mark.django_db
def test_list_customer_addresses_empty(api_client):
    customer = _create_customer()
    _auth(api_client, customer)

    response = api_client.get("/api/v1/accounts/customer/addresses/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_create_and_list_customer_addresses(api_client):
    customer = _create_customer("customer_addr_crud")
    _auth(api_client, customer)

    create_response = api_client.post(
        "/api/v1/accounts/customer/addresses/",
        {
            "label": "Casa",
            "address": "Calle 50 # 10-20",
            "latitude": 4.65,
            "longitude": -74.08,
            "is_default": True,
        },
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data["label"] == "Casa"
    assert create_response.data["is_default"] is True
    address_id = create_response.data["id"]

    list_response = api_client.get("/api/v1/accounts/customer/addresses/")
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) == 1
    assert list_response.data[0]["id"] == address_id


@pytest.mark.django_db
def test_update_customer_address(api_client):
    customer = _create_customer("customer_addr_update")
    _auth(api_client, customer)
    address = CustomerAddress.objects.create(
        user=customer,
        label="Oficina",
        address="Carrera 7 # 80-50",
        latitude=4.67,
        longitude=-74.05,
        is_default=False,
    )

    response = api_client.patch(
        f"/api/v1/accounts/customer/addresses/{address.id}/",
        {"label": "Trabajo", "is_default": True},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["label"] == "Trabajo"
    assert response.data["is_default"] is True


@pytest.mark.django_db
def test_delete_customer_address(api_client):
    customer = _create_customer("customer_addr_delete")
    _auth(api_client, customer)
    address = CustomerAddress.objects.create(
        user=customer,
        label="Temporal",
        address="Calle 1",
        latitude=4.6,
        longitude=-74.0,
    )

    response = api_client.delete(f"/api/v1/accounts/customer/addresses/{address.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not CustomerAddress.objects.filter(id=address.id).exists()


@pytest.mark.django_db
def test_customer_cannot_access_other_address(api_client):
    owner = _create_customer("customer_addr_owner")
    other = _create_customer("customer_addr_other")
    address = CustomerAddress.objects.create(
        user=owner,
        label="Privada",
        address="Calle privada",
        latitude=4.6,
        longitude=-74.0,
    )

    _auth(api_client, other)
    response = api_client.patch(
        f"/api/v1/accounts/customer/addresses/{address.id}/",
        {"label": "Hack"},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
