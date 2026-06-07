from datetime import datetime, timedelta, timezone

import pytest

from features.accounts.domain.exceptions import (
    VerificationTokenAlreadyUsedError,
    VerificationTokenExpiredError,
)
from features.accounts.domain.verification_token import EmailVerificationToken


def test_verification_token_expired_raises():
    token = EmailVerificationToken(
        user_id=1,
        token="abc-123",
        expires_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)

    with pytest.raises(VerificationTokenExpiredError, match="expirado"):
        token.validate_for_use(now)


def test_verification_token_already_used_raises():
    token = EmailVerificationToken(
        user_id=1,
        token="abc-123",
        expires_at=datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc),
        used_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)

    with pytest.raises(VerificationTokenAlreadyUsedError, match="utilizado"):
        token.validate_for_use(now)


def test_verification_token_valid_passes():
    token = EmailVerificationToken(
        user_id=1,
        token="abc-123",
        expires_at=datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)

    token.validate_for_use(now)
