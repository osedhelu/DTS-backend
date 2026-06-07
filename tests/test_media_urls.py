import pytest
from django.test import override_settings

from core.media_urls import build_public_media_url


@override_settings(MEDIA_PUBLIC_BASE_URL="http://extreme.local:8000")
def test_build_public_media_url_returns_absolute_when_base_configured():
    assert (
        build_public_media_url("/media/stores/1/logo.png")
        == "http://extreme.local:8000/media/stores/1/logo.png"
    )


@override_settings(MEDIA_PUBLIC_BASE_URL="")
def test_build_public_media_url_keeps_relative_without_base():
    assert build_public_media_url("/media/stores/1/logo.png") == "/media/stores/1/logo.png"


def test_build_public_media_url_passes_through_absolute():
    url = "https://cdn.example.com/logo.png"
    assert build_public_media_url(url) == url
