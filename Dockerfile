# Imagen para Railway / deploy standalone del submódulo backend.
# PostGIS en Django requiere GDAL/GEOS — no usar Railpack/Nixpacks.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV DJANGO_SETTINGS_MODULE=core.settings \
    SECRET_KEY=collectstatic-build-only \
    DB_HOST=localhost \
    DB_NAME=dts_delivery \
    DB_USER=postgres \
    DB_PASSWORD=postgres
RUN uv run --no-dev python manage.py collectstatic --noinput

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
# Daphne + ASGI para HTTP y WebSockets (Channels). Gunicorn/WSGI no hace upgrade WS.
CMD ["sh", "-c", "uv run daphne -b 0.0.0.0 -p ${PORT:-8000} core.asgi:application"]
