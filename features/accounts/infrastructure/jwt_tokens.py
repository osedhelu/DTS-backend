"""Emisión de JWT con los mismos claims que el login por password."""

from __future__ import annotations

from typing import Any

from rest_framework_simplejwt.tokens import RefreshToken


def build_refresh_token_for_user(user: Any) -> RefreshToken:
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["email"] = user.email
    refresh["user_id"] = user.id
    return refresh


def issue_tokens_for_user(user: Any) -> dict[str, str]:
    refresh = build_refresh_token_for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
