from datetime import timedelta

import pytest
from django.utils import timezone

from features.accounts.application.use_cases.verify_email import VerifyEmailUseCase
from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import VerificationTokenNotFoundError
from features.accounts.infrastructure.models import CustomUser, EmailVerificationToken
from features.accounts.infrastructure.verification_token_repository import (
    DjangoEmailVerificationTokenRepository,
)


@pytest.mark.django_db
def test_verify_email_activates_merchant():
    user = CustomUser.objects.create_user(
        username="verify_merchant",
        email="verify@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
        email_verified=False,
        is_active=False,
    )
    token_model = EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=24),
    )

    use_case = VerifyEmailUseCase(DjangoEmailVerificationTokenRepository())
    activated = use_case.execute(str(token_model.token))

    user.refresh_from_db()
    token_model.refresh_from_db()
    assert activated.email_verified is True
    assert user.email_verified is True
    assert user.is_active is True
    assert token_model.used_at is not None


@pytest.mark.django_db
def test_verify_email_invalid_token_raises():
    use_case = VerifyEmailUseCase(DjangoEmailVerificationTokenRepository())

    with pytest.raises(VerificationTokenNotFoundError):
        use_case.execute("00000000-0000-0000-0000-000000000000")
