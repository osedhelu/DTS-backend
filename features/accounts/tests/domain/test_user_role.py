from features.accounts.domain.entities import UserRole


def test_user_role_values():
    assert UserRole.SUPER_ADMIN == "super_admin"
    assert UserRole.MERCHANT == "merchant"
    assert UserRole.DRIVER == "driver"
    assert UserRole.CUSTOMER == "customer"
    assert len(UserRole) == 4
