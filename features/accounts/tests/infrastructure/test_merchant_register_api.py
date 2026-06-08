from datetime import timedelta
from pathlib import Path

import pytest
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework import status

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, EmailVerificationToken
from features.accounts.infrastructure.tasks import send_merchant_verification_email

BACKEND_DIR = Path(__file__).resolve().parents[4]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_merchant_api"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.gdal import GDAL_VERSION  # noqa: F401
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


MERCHANT_REGISTER_PAYLOAD = {
    "email": "public_merchant@test.com",
    "password": "securepass123",
    "first_name": "Carlos",
    "last_name": "Ruiz",
    "store_name": "Tacos Carlos",
    "vertical": "FOOD",
    "category_template": "Comida rápida",
    "phone": "+573001112233",
    "latitude": 4.711,
    "longitude": -74.0721,
}

ACCOUNTS_URLCONF = "features.accounts.tests.urls"


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_merchant_public_register_201(api_client, mailoutbox):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        WEB_URL="http://localhost:3000",
        ROOT_URLCONF=ACCOUNTS_URLCONF,
    ):
        response = api_client.post(
            "/api/v1/accounts/merchant/register/",
            MERCHANT_REGISTER_PAYLOAD,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "public_merchant@test.com"
        assert "store_id" in response.data
        user = CustomUser.objects.get(email="public_merchant@test.com")
        assert user.email_verified is False
        assert len(mailoutbox) == 1
        assert "confirmar-email" in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_merchant_register_duplicate_email_400(api_client):
    CustomUser.objects.create_user(
        username="existing",
        email="dup@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )

    payload = {**MERCHANT_REGISTER_PAYLOAD, "email": "dup@test.com"}
    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/merchant/register/",
            payload,
            format="json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "dup@test.com" in response.data["detail"]


@pytest.mark.django_db
def test_verify_email_api_200(api_client):
    user = CustomUser.objects.create_user(
        username="api_verify",
        email="api_verify@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
        email_verified=False,
        is_active=False,
    )
    token = EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=24),
    )

    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/verify-email/",
            {"token": str(token.token)},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.email_verified is True
    assert user.is_active is True


@pytest.mark.django_db
def test_verify_email_invalid_token_400(api_client):
    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/verify-email/",
            {"token": "00000000-0000-0000-0000-000000000000"},
            format="json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_resend_verification_email(api_client, mailoutbox):
    user = CustomUser.objects.create_user(
        username="resend_user",
        email="resend@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
        email_verified=False,
        is_active=False,
    )

    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/resend-verification/",
            {"email": user.email},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["resend@test.com"]
    assert EmailVerificationToken.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_send_verification_email_task(mailoutbox):
    user = CustomUser.objects.create_user(
        username="task_merchant",
        email="task_merchant@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )
    from features.accounts.infrastructure.models import MerchantProfile

    MerchantProfile.objects.create(
        user=user,
        business_name="Tienda Task",
        phone="+573001112233",
    )
    token = "00000000-0000-0000-0000-000000000001"

    result = send_merchant_verification_email(user.id, token)

    assert result == "sent:task_merchant@test.com"
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to == ["task_merchant@test.com"]
    assert token in email.alternatives[0][0]
