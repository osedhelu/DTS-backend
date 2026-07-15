from enum import StrEnum


class NotificationRecipient(StrEnum):
    CUSTOMER = "customer"
    ONLINE_DRIVERS = "online_drivers"
    ASSIGNED_DRIVER = "assigned_driver"
