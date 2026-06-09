"""Sirve archivos de MEDIA usando el mismo StorageBackend que las subidas."""

import mimetypes

from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from core.storage import get_storage_backend


@require_GET
def serve_media_file(request, path: str) -> HttpResponse:
    backend = get_storage_backend()
    if not backend.exists(path):
        raise Http404(f"Archivo de media no encontrado: {path}")

    content_type, _encoding = mimetypes.guess_type(path)
    return HttpResponse(
        backend.read(path),
        content_type=content_type or "application/octet-stream",
    )
