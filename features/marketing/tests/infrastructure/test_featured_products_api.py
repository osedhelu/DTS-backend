import pytest
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.test import APIRequestFactory

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.marketing.infrastructure.views import FeaturedProductsView
from features.products.domain.entities import ProductType
from features.products.infrastructure.models import Product
from features.stores.domain.entities import StoreStatus, StoreVertical
from features.stores.infrastructure.models import Store


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
def test_featured_products_returns_active_from_open_stores(api_factory):
    owner = CustomUser.objects.create_user(
        username="feat_owner",
        email="feat_owner@test.com",
        password="x",
        role=UserRole.MERCHANT,
    )
    open_store = Store.objects.create(
        owner=owner,
        name="Tienda Abierta",
        status=StoreStatus.OPEN,
        vertical=StoreVertical.FOOD,
        location=Point(0, 0, srid=4326),
        is_active=True,
    )
    closed_store = Store.objects.create(
        owner=owner,
        name="Tienda Cerrada",
        status=StoreStatus.CLOSED,
        vertical=StoreVertical.FOOD,
        location=Point(0.1, 0.1, srid=4326),
        is_active=True,
    )
    active = Product.objects.create(
        store=open_store,
        name="Burger",
        price="10.00",
        stock=5,
        product_type=ProductType.PHYSICAL,
        is_active=True,
    )
    Product.objects.create(
        store=open_store,
        name="Hidden",
        price="1.00",
        stock=1,
        product_type=ProductType.PHYSICAL,
        is_active=False,
    )
    Product.objects.create(
        store=closed_store,
        name="Only closed",
        price="2.00",
        stock=1,
        product_type=ProductType.PHYSICAL,
        is_active=True,
    )

    request = api_factory.get("/api/v1/marketing/featured-products/")
    response = FeaturedProductsView.as_view()(request)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == active.id
    assert response.data[0]["name"] == "Burger"
    assert response.data[0]["store_id"] == open_store.id
    assert response.data[0]["store_name"] == "Tienda Abierta"


@pytest.mark.django_db
def test_featured_products_allows_anonymous(api_factory):
    request = api_factory.get("/api/v1/marketing/featured-products/")
    response = FeaturedProductsView.as_view()(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == []
