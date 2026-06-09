from datetime import timedelta

import pytest
from django.utils import timezone

from features.accounts.application.use_cases.confirm_password_reset import (
    ConfirmPasswordResetUseCase,
)
from features.accounts.application.use_cases.request_password_reset import (
    RequestPasswordResetUseCase,
)
from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import PasswordResetTokenNotFoundError
from features.accounts.infrastructure.models import CustomUser, PasswordResetToken
from features.accounts.infrastructure.password_reset_token_repository import (
    DjangoPasswordResetTokenRepository,
)


@pytest.mark.django_db
def test_request_password_reset_creates_token_for_existing_user():
    user = CustomUser.objects.create_user(
        username="reset_user",
        email="reset@test.com",
        password="oldpassword123",
        role=UserRole.MERCHANT,
    )

    use_case = RequestPasswordResetUseCase(DjangoPasswordResetTokenRepository())
    result = use_case.execute(user.email)

    assert result.user_id == user.id
    assert result.token is not None
    assert PasswordResetToken.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_request_password_reset_unknown_email_returns_generic_message():
    use_case = RequestPasswordResetUseCase(DjangoPasswordResetTokenRepository())
    result = use_case.execute("unknown@test.com")

    assert result.user_id is None
    assert result.token is None
    assert PasswordResetToken.objects.count() == 0


@pytest.mark.django_db
def test_confirm_password_reset_updates_password():
    user = CustomUser.objects.create_user(
        username="confirm_reset",
        email="confirm_reset@test.com",
        password="oldpassword123",
        role=UserRole.SUPER_ADMIN,
    )
    token_model = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=1),
    )

    use_case = ConfirmPasswordResetUseCase(DjangoPasswordResetTokenRepository())
    use_case.execute(str(token_model.token), "newpassword456")

    user.refresh_from_db()
    token_model.refresh_from_db()
    assert user.check_password("newpassword456") is True
    assert token_model.used_at is not None


@pytest.mark.django_db
def test_confirm_password_reset_invalid_token_raises():
    use_case = ConfirmPasswordResetUseCase(DjangoPasswordResetTokenRepository())

    with pytest.raises(PasswordResetTokenNotFoundError):
        use_case.execute("00000000-0000-0000-0000-000000000000", "newpassword456")
