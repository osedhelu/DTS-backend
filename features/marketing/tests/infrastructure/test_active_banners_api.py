import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from features.marketing.infrastructure.models import BannerModel
from features.marketing.infrastructure.views import ActiveBannersView


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
def test_active_banners_api_returns_only_active_sorted_banners(api_factory):
    BannerModel.objects.create(
        title="Inactivo",
        image_url="https://cdn.example.com/inactive.jpg",
        is_active=False,
        sort_order=0,
    )
    second = BannerModel.objects.create(
        title="Promo 2",
        image_url="https://cdn.example.com/banner2.jpg",
        link_url="https://example.com/promo2",
        is_active=True,
        sort_order=2,
    )
    first = BannerModel.objects.create(
        title="Promo 1",
        image_url="https://cdn.example.com/banner1.jpg",
        link_url="https://example.com/promo1",
        is_active=True,
        sort_order=1,
    )

    request = api_factory.get("/api/v1/marketing/banners/active/")
    response = ActiveBannersView.as_view()(request)

    assert response.status_code == status.HTTP_200_OK
    payload = response.data
    assert len(payload) == 2
    assert payload[0]["id"] == first.id
    assert payload[0]["title"] == "Promo 1"
    assert payload[1]["id"] == second.id
    assert payload[1]["title"] == "Promo 2"


@pytest.mark.django_db
def test_active_banners_api_allows_anonymous_access(api_factory):
    BannerModel.objects.create(
        title="Promo pública",
        image_url="https://cdn.example.com/public.jpg",
        is_active=True,
        sort_order=0,
    )

    request = api_factory.get("/api/v1/marketing/banners/active/")
    response = ActiveBannersView.as_view()(request)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
