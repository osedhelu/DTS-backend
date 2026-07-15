from features.delivery.domain.repositories import DriverAvailabilityRepository
from features.notifications.domain.services import OrderStatusNotificationMapper
from features.notifications.domain.value_objects import NotificationRecipient
from features.orders.domain.entities import Order
from features.orders.domain.value_objects import OrderStatus


def resolve_recipient_user_ids(
    order: Order,
    order_status: OrderStatus,
    driver_availability_repository: DriverAvailabilityRepository,
) -> list[int]:
    recipients = OrderStatusNotificationMapper.recipients_for_status(order_status)
    if not recipients:
        return []

    user_ids: list[int] = []

    if NotificationRecipient.CUSTOMER in recipients:
        user_ids.append(order.customer_id)

    if NotificationRecipient.ONLINE_DRIVERS in recipients:
        online_drivers = driver_availability_repository.list_online_drivers()
        user_ids.extend(driver.driver_id for driver in online_drivers)

    if NotificationRecipient.ASSIGNED_DRIVER in recipients and order.driver_id is not None:
        user_ids.append(order.driver_id)

    # Deduplicar conservando orden
    seen: set[int] = set()
    unique: list[int] = []
    for uid in user_ids:
        if uid not in seen:
            seen.add(uid)
            unique.append(uid)
    return unique
