from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.chat.application.participants import (
    other_chat_participant_ids,
    user_is_chat_participant,
)
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store
import pytest


@pytest.mark.django_db
def test_merchant_owner_is_chat_participant():
    merchant = CustomUser.objects.create_user(
        username="m_part",
        email="m_part@test.com",
        password="x",
        role=UserRole.MERCHANT,
    )
    other = CustomUser.objects.create_user(
        username="m_other",
        email="m_other@test.com",
        password="x",
        role=UserRole.MERCHANT,
    )
    customer = CustomUser.objects.create_user(
        username="c_part",
        email="c_part@test.com",
        password="x",
        role=UserRole.CUSTOMER,
    )
    driver = CustomUser.objects.create_user(
        username="d_part",
        email="d_part@test.com",
        password="x",
        role=UserRole.DRIVER,
    )
    store = Store(owner=merchant, name="P", status=StoreStatus.OPEN)
    store.set_location(GeoLocation(latitude=1, longitude=1))
    store.save()
    order = Order.objects.create(
        customer=customer,
        store=store,
        driver=driver,
        status=OrderStatus.ON_THE_WAY,
        total="1.00",
    )
    order = Order.objects.select_related("store").get(pk=order.pk)

    assert user_is_chat_participant(order, merchant.id)
    assert user_is_chat_participant(order, customer.id)
    assert user_is_chat_participant(order, driver.id)
    assert not user_is_chat_participant(order, other.id)

    others = other_chat_participant_ids(order, driver.id)
    assert set(others) == {customer.id, merchant.id}
