import pytest
from django.test import Client, override_settings

from tests.gis_helpers import gdal_available

pytestmark = pytest.mark.skipif(
    not gdal_available(),
    reason="GDAL requerido en local/CI para cargar apps GIS",
)


def test_serve_media_when_enabled(tmp_path):
    media_file = tmp_path / "stores" / "1" / "logo.png"
    media_file.parent.mkdir(parents=True)
    media_file.write_bytes(b"fake-png")

    client = Client()

    with override_settings(
        SERVE_MEDIA=True,
        MEDIA_ROOT=tmp_path,
        MEDIA_URL="/media/",
    ):
        response = client.get("/media/stores/1/logo.png")

    assert response.status_code == 200
    assert response.content == b"fake-png"


def test_media_not_served_when_disabled(tmp_path):
    media_file = tmp_path / "stores" / "1" / "logo.png"
    media_file.parent.mkdir(parents=True)
    media_file.write_bytes(b"fake-png")

    client = Client()

    with override_settings(
        SERVE_MEDIA=False,
        MEDIA_ROOT=tmp_path,
        MEDIA_URL="/media/",
    ):
        response = client.get("/media/stores/1/logo.png")

    assert response.status_code == 404
