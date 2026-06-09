import pytest
from django.test.utils import override_settings
from rest_framework import status

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, PasswordResetToken
from features.accounts.infrastructure.tasks import send_password_reset_email
from features.accounts.tests.urls import ACCOUNTS_URLCONF


@pytest.mark.django_db
def test_password_reset_request_sends_email(api_client, mailoutbox):
    user = CustomUser.objects.create_user(
        username="merchant_reset",
        email="merchant_reset@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )

    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/password-reset/request/",
            {"email": user.email},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert "recibirás un enlace" in response.data["detail"]
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [user.email]
    assert PasswordResetToken.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_password_reset_request_unknown_email_same_response(api_client, mailoutbox):
    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/password-reset/request/",
            {"email": "missing@test.com"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert len(mailoutbox) == 0
    assert PasswordResetToken.objects.count() == 0


@pytest.mark.django_db
def test_password_reset_confirm_success(api_client):
    from datetime import timedelta

    from django.utils import timezone

    user = CustomUser.objects.create_user(
        username="confirm_api",
        email="confirm_api@test.com",
        password="oldpassword123",
        role=UserRole.MERCHANT,
    )
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=1),
    )

    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/password-reset/confirm/",
            {"token": str(token.token), "password": "newpassword789"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password("newpassword789") is True


@pytest.mark.django_db
def test_password_reset_confirm_invalid_token_400(api_client):
    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        response = api_client.post(
            "/api/v1/accounts/password-reset/confirm/",
            {
                "token": "00000000-0000-0000-0000-000000000000",
                "password": "newpassword789",
            },
            format="json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_send_password_reset_email_task(mailoutbox):
    user = CustomUser.objects.create_user(
        username="task_reset",
        email="task_reset@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )
    token = "00000000-0000-0000-0000-000000000001"

    result = send_password_reset_email(user.id, token)

    assert result == "sent:task_reset@test.com"
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to == ["task_reset@test.com"]
    assert token in email.alternatives[0][0]
