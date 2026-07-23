from features.delivery.domain.repositories import DriverAvailabilityRepository
from features.delivery.domain.services import DriverMatcher
from features.notifications.domain.services import OrderStatusNotificationMapper
from features.notifications.domain.value_objects import NotificationRecipient
from features.orders.domain.entities import Order
from features.orders.domain.value_objects import OrderStatus
from features.stores.domain.value_objects import GeoLocation


def resolve_recipient_user_ids(
    order: Order,
    order_status: OrderStatus,
    driver_availability_repository: DriverAvailabilityRepository,
    *,
    pickup_location: GeoLocation | None = None,
) -> list[int]:
    recipients = OrderStatusNotificationMapper.recipients_for_status(order_status)
    if not recipients:
        return []

    user_ids: list[int] = []

    if NotificationRecipient.CUSTOMER in recipients:
        user_ids.append(order.customer_id)

    if NotificationRecipient.ONLINE_DRIVERS in recipients:
        online_drivers = driver_availability_repository.list_online_drivers()
        if pickup_location is None:
            # Sin ubicación de tienda no se notifica a conductores (evita spam global).
            online_drivers = []
        else:
            online_drivers = [
                driver
                for driver in online_drivers
                if DriverMatcher.driver_covers_store(driver, pickup_location)
            ]
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
