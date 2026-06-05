from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver

from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order

order_status_changed = Signal()


@receiver(pre_save, sender=Order)
def capture_previous_order_status(sender, instance: Order, **kwargs) -> None:
    if not instance.pk:
        instance._previous_status = None
        return

    previous_status = (
        Order.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    )
    instance._previous_status = previous_status


@receiver(post_save, sender=Order)
def detect_order_status_change(sender, instance: Order, created: bool, **kwargs) -> None:
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)
    if previous_status is None or previous_status == instance.status:
        return

    order_status_changed.send(
        sender=sender,
        order_id=instance.pk,
        previous_status=previous_status,
        current_status=instance.status,
    )


@receiver(order_status_changed)
def enqueue_assign_driver_on_ready_for_pickup(
    sender,
    order_id: int,
    previous_status: str,
    current_status: str,
    **kwargs,
) -> None:
    if current_status != OrderStatus.READY_FOR_PICKUP:
        return

    from features.delivery.infrastructure.tasks import assign_driver_task

    assign_driver_task.delay(order_id)


@receiver(order_status_changed)
def enqueue_notify_customer_on_the_way(
    sender,
    order_id: int,
    previous_status: str,
    current_status: str,
    **kwargs,
) -> None:
    if current_status != OrderStatus.ON_THE_WAY:
        return

    from features.notifications.infrastructure.tasks import notify_customer_task

    notify_customer_task.delay(order_id)
