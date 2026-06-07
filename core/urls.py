from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.api.v1.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
