from datetime import timedelta

import pytest
from django.utils import timezone

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, EmailVerificationToken


@pytest.mark.django_db
def test_verification_token_persistence():
    user = CustomUser.objects.create_user(
        username="merchant_token",
        email="token@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )
    expires_at = timezone.now() + timedelta(hours=24)

    token = EmailVerificationToken.objects.create(user=user, expires_at=expires_at)

    assert token.token is not None
    assert token.used_at is None
    assert token.expires_at == expires_at
    assert EmailVerificationToken.objects.filter(user=user, token=token.token).exists()
