"""Helpers de acceso al chat de pedido (customer, driver, merchant owner)."""

from __future__ import annotations

from features.chat.domain.exceptions import UnauthorizedChatAccessError
from features.orders.infrastructure.models import Order as OrderModel


def user_is_chat_participant(order: OrderModel, user_id: int) -> bool:
    if order.customer_id == user_id:
        return True
    if order.driver_id is not None and order.driver_id == user_id:
        return True
    store = getattr(order, "store", None)
    if store is not None and getattr(store, "owner_id", None) == user_id:
        return True
    # Lazy load store.owner_id if store not select_related
    if store is None and order.store_id:
        from features.stores.infrastructure.models import Store

        owner_id = (
            Store.objects.filter(pk=order.store_id)
            .values_list("owner_id", flat=True)
            .first()
        )
        if owner_id == user_id:
            return True
    return False


def assert_chat_participant(order: OrderModel, user_id: int) -> None:
    if user_is_chat_participant(order, user_id):
        return
    raise UnauthorizedChatAccessError("No tienes acceso al chat de este pedido")


def other_chat_participant_ids(order: OrderModel, sender_id: int) -> list[int]:
    """IDs de los demás participantes del pedido (excluye al emisor)."""
    ids: set[int] = {order.customer_id}
    if order.driver_id is not None:
        ids.add(order.driver_id)
    store = getattr(order, "store", None)
    if store is not None and getattr(store, "owner_id", None):
        ids.add(store.owner_id)
    elif order.store_id:
        from features.stores.infrastructure.models import Store

        owner_id = (
            Store.objects.filter(pk=order.store_id)
            .values_list("owner_id", flat=True)
            .first()
        )
        if owner_id:
            ids.add(owner_id)
    ids.discard(sender_id)
    return sorted(ids)
