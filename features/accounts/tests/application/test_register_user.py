from unittest.mock import MagicMock

import pytest

from features.accounts.application.dto import RegisterUserDTO
from features.accounts.application.use_cases.register_user import RegisterUserUseCase
from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import DuplicateEmailError


def test_register_merchant():
    repository = MagicMock()
    repository.exists_by_email.return_value = False
    repository.register.return_value = {"id": 1, "role": UserRole.MERCHANT}

    use_case = RegisterUserUseCase(repository)
    dto = RegisterUserDTO(
        username="merchant_shop",
        email="shop@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
        phone="+573001112233",
        business_name="Restaurante El Buen Sabor",
        tax_id="900123456",
        address="Calle 10 #20-30",
    )

    result = use_case.execute(dto)

    repository.exists_by_email.assert_called_once_with("shop@test.com")
    repository.register.assert_called_once_with(
        {
            "username": "merchant_shop",
            "email": "shop@test.com",
            "password": "securepass123",
            "role": UserRole.MERCHANT,
            "phone": "+573001112233",
            "business_name": "Restaurante El Buen Sabor",
            "tax_id": "900123456",
            "address": "Calle 10 #20-30",
            "license_number": "",
            "vehicle_type": "",
            "default_address": "",
        }
    )
    assert result == {"id": 1, "role": UserRole.MERCHANT}


def test_register_duplicate_email():
    repository = MagicMock()
    repository.exists_by_email.return_value = True

    use_case = RegisterUserUseCase(repository)
    dto = RegisterUserDTO(
        username="merchant_shop",
        email="shop@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
        phone="+573001112233",
        business_name="Restaurante El Buen Sabor",
    )

    with pytest.raises(DuplicateEmailError, match="shop@test.com"):
        use_case.execute(dto)

    repository.register.assert_not_called()
