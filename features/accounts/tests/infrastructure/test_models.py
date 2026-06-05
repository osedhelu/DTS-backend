import pytest

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser


@pytest.mark.django_db
def test_create_user_per_role():
    roles_data = {
        UserRole.SUPER_ADMIN: {"username": "admin1", "email": "admin@test.com"},
        UserRole.MERCHANT: {"username": "merchant1", "email": "merchant@test.com"},
        UserRole.DRIVER: {"username": "driver1", "email": "driver@test.com"},
        UserRole.CUSTOMER: {"username": "customer1", "email": "customer@test.com"},
    }

    for role, data in roles_data.items():
        user = CustomUser.objects.create_user(
            username=data["username"],
            email=data["email"],
            password="securepass123",
            role=role,
        )
        assert user.role == role
        assert user.check_password("securepass123")
        assert user.email == data["email"]


@pytest.mark.django_db
def test_create_superuser_sets_super_admin_role():
    user = CustomUser.objects.create_superuser(
        username="superadmin",
        email="superadmin@test.com",
        password="securepass123",
    )
    assert user.role == UserRole.SUPER_ADMIN
    assert user.is_staff is True
    assert user.is_superuser is True
