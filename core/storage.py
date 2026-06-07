"""Abstracción de almacenamiento de medios — local (dev) / S3 (prod)."""

from __future__ import annotations

import mimetypes
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Protocol, runtime_checkable

from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@runtime_checkable
class StorageBackend(Protocol):
    def save(self, name: str, content: object) -> str: ...

    def delete(self, name: str) -> None: ...

    def exists(self, name: str) -> bool: ...

    def url(self, name: str) -> str: ...

    def read(self, name: str) -> bytes: ...


def read_file_content(content: object) -> bytes:
    if hasattr(content, "chunks"):
        return b"".join(chunk for chunk in content.chunks())  # type: ignore[union-attr]

    if hasattr(content, "read"):
        data = content.read()  # type: ignore[union-attr]
        if hasattr(content, "seek"):
            content.seek(0)  # type: ignore[union-attr]
        return data

    if isinstance(content, bytes):
        return content

    raise TypeError(f"Tipo de contenido no soportado: {type(content)!r}")


class LocalStorageBackend:
    def __init__(self, media_root: Path | str, media_url: str = "/media/") -> None:
        self.media_root = Path(media_root)
        self.media_url = media_url if media_url.endswith("/") else f"{media_url}/"

    def save(self, name: str, content: object) -> str:
        destination = self.media_root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(read_file_content(content))
        return name

    def delete(self, name: str) -> None:
        path = self.media_root / name
        if path.exists():
            path.unlink()

    def exists(self, name: str) -> bool:
        return (self.media_root / name).exists()

    def url(self, name: str) -> str:
        return f"{self.media_url}{name}"

    def read(self, name: str) -> bytes:
        return (self.media_root / name).read_bytes()


class S3StorageBackend:
    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        custom_domain: str = "",
        client: object | None = None,
    ) -> None:
        self.bucket = bucket
        self.region = region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self.custom_domain = custom_domain.rstrip("/")
        self._client = client

        if not bucket:
            raise ValueError("AWS_STORAGE_BUCKET_NAME es obligatorio para S3")
        if client is None and (not access_key_id or not secret_access_key):
            raise ValueError("Credenciales AWS requeridas para S3")

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._secret_access_key,
            )
        return self._client

    def save(self, name: str, content: object) -> str:
        body = read_file_content(content)
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        self.client.put_object(
            Bucket=self.bucket,
            Key=name,
            Body=body,
            ContentType=content_type,
        )
        return name

    def delete(self, name: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=name)

    def exists(self, name: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=name)
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def url(self, name: str) -> str:
        if self.custom_domain:
            return f"{self.custom_domain}/{name}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{name}"

    def read(self, name: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=name)
        body = response["Body"].read()
        return body if isinstance(body, bytes) else body.encode()


def build_storage_backend(
    *,
    backend: str,
    media_root: Path | str,
    media_url: str,
    aws_access_key_id: str = "",
    aws_secret_access_key: str = "",
    aws_storage_bucket_name: str = "",
    aws_s3_region_name: str = "us-east-1",
    aws_s3_custom_domain: str = "",
    s3_client: object | None = None,
) -> StorageBackend:
    normalized = backend.lower().strip()

    if normalized == "s3":
        return S3StorageBackend(
            bucket=aws_storage_bucket_name,
            region=aws_s3_region_name,
            access_key_id=aws_access_key_id,
            secret_access_key=aws_secret_access_key,
            custom_domain=aws_s3_custom_domain,
            client=s3_client,
        )

    if normalized != "local":
        raise ValueError(f"MEDIA_STORAGE_BACKEND no soportado: {backend}")

    return LocalStorageBackend(media_root=media_root, media_url=media_url)


def get_storage_backend() -> StorageBackend:
    from django.conf import settings

    return build_storage_backend(
        backend=getattr(settings, "MEDIA_STORAGE_BACKEND", "local"),
        media_root=getattr(settings, "MEDIA_ROOT", Path("media")),
        media_url=getattr(settings, "MEDIA_URL", "/media/"),
        aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", ""),
        aws_storage_bucket_name=getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""),
        aws_s3_region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
        aws_s3_custom_domain=getattr(settings, "AWS_S3_CUSTOM_DOMAIN", ""),
    )


@deconstructible
class DjangoMediaStorage(Storage):
    """Adaptador Django Storage → StorageBackend (ProductImage, Store.logo)."""

    def __init__(self) -> None:
        self._backend: StorageBackend | None = None

    @property
    def backend(self) -> StorageBackend:
        if self._backend is None:
            self._backend = get_storage_backend()
        return self._backend

    def _open(self, name: str, mode: str = "rb") -> BinaryIO:
        if "b" not in mode:
            raise ValueError("Solo se admite lectura binaria")
        return BytesIO(self.backend.read(name))

    def _save(self, name: str, content: object) -> str:
        return self.backend.save(name, content)

    def delete(self, name: str) -> None:
        self.backend.delete(name)

    def exists(self, name: str) -> bool:
        return self.backend.exists(name)

    def url(self, name: str) -> str:
        if not name:
            return ""
        return self.backend.url(name)

    def size(self, name: str) -> int:
        return len(self.backend.read(name))
