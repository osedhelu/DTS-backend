from enum import StrEnum


class UserRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    MERCHANT = "merchant"
    DRIVER = "driver"
    CUSTOMER = "customer"
