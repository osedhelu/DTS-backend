from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from core.storage import (
    DjangoMediaStorage,
    LocalStorageBackend,
    S3StorageBackend,
    build_storage_backend,
)


def test_local_storage_save(tmp_path: Path):
    backend = LocalStorageBackend(media_root=tmp_path, media_url="/media/")
    content = SimpleUploadedFile("photo.png", b"fake-png-bytes", content_type="image/png")

    saved_name = backend.save("products/1/photo.png", content)

    assert saved_name == "products/1/photo.png"
    assert (tmp_path / "products/1/photo.png").read_bytes() == b"fake-png-bytes"
    assert backend.exists(saved_name)
    assert backend.url(saved_name) == "/media/products/1/photo.png"
    assert backend.read(saved_name) == b"fake-png-bytes"

    backend.delete(saved_name)
    assert not backend.exists(saved_name)


def test_s3_storage_upload_mock():
    mock_client = MagicMock()
    backend = S3StorageBackend(
        bucket="dts-media",
        region="us-east-1",
        access_key_id="test-key",
        secret_access_key="test-secret",
        client=mock_client,
    )
    content = SimpleUploadedFile("logo.png", b"logo-bytes", content_type="image/png")

    saved_name = backend.save("stores/1/logo.png", content)

    assert saved_name == "stores/1/logo.png"
    mock_client.put_object.assert_called_once_with(
        Bucket="dts-media",
        Key="stores/1/logo.png",
        Body=b"logo-bytes",
        ContentType="image/png",
    )
    assert backend.url(saved_name) == "https://dts-media.s3.us-east-1.amazonaws.com/stores/1/logo.png"

    mock_client.head_object.return_value = {"ContentLength": 10}
    assert backend.exists(saved_name) is True

    mock_client.get_object.return_value = {"Body": BytesIO(b"logo-bytes")}
    assert backend.read(saved_name) == b"logo-bytes"

    backend.delete(saved_name)
    mock_client.delete_object.assert_called_once_with(
        Bucket="dts-media",
        Key="stores/1/logo.png",
    )


def test_django_media_storage_uses_local_backend(tmp_path: Path):
    from django.test.utils import override_settings

    with override_settings(
        MEDIA_ROOT=tmp_path,
        MEDIA_URL="/media/",
        MEDIA_STORAGE_BACKEND="local",
    ):
        storage = DjangoMediaStorage()
        storage._backend = None  # reset cached backend
        content = SimpleUploadedFile("item.jpg", b"jpeg-data", content_type="image/jpeg")
        saved_name = storage.save("products/9/item.jpg", content)

    assert saved_name == "products/9/item.jpg"
    assert (tmp_path / "products/9/item.jpg").exists()
    assert storage.url(saved_name) == "/media/products/9/item.jpg"


def test_build_storage_backend_rejects_unknown():
    with pytest.raises(ValueError, match="no soportado"):
        build_storage_backend(
            backend="cloudinary",
            media_root="/tmp",
            media_url="/media/",
        )
