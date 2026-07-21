"""Sincroniza estado open/closed de tiendas según horarios."""

from celery import shared_task

from features.stores.domain.entities import StoreStatus
from features.stores.domain.services import OpeningHoursService, OpeningHoursSlot
from features.stores.infrastructure.models import Store, StoreOpeningHours


def execute_sync_store_hours() -> str:
    updated = 0
    stores = Store.objects.filter(use_schedule=True, is_active=True)
    for store in stores:
        rows = StoreOpeningHours.objects.filter(store_id=store.id)
        slots = [
            OpeningHoursSlot(
                day_of_week=row.day_of_week,
                open_time=row.open_time,
                close_time=row.close_time,
                is_closed=row.is_closed,
            )
            for row in rows
        ]
        if not slots:
            continue

        should_open = OpeningHoursService.is_open_now(slots)
        target = StoreStatus.OPEN if should_open else StoreStatus.CLOSED
        if store.status != target.value:
            store.status = target.value
            store.save(update_fields=["status", "updated_at"])
            updated += 1

    return f"synced:{updated}"


@shared_task(
    bind=True,
    max_retries=2,
    name="features.stores.infrastructure.tasks.sync_store_hours_task",
)
def sync_store_hours_task(self) -> str:
    return execute_sync_store_hours()
