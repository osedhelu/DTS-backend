# DTS Backend

API REST Django (DRF). Submódulo del monorepo [DTS-E-Commerce](../README.md).

El frontend administrativo vive en `web-admin/` (Next.js), no en este proyecto.

## Setup local

```bash
cp .env.example .env
uv sync
```

Requiere PostGIS y Redis (`make docker-up` desde la raíz del monorepo).

## Comandos

```bash
make test       # pytest
make migrate    # migraciones
make run        # runserver :8000
```

## Deploy en Railway

Este submódulo tiene su propio `Dockerfile` + `railway.toml`.

1. Conecta en Railway el **repo del backend** (no el monorepo).
2. Root Directory: `/`
3. Push incluye `railway.toml` y `Dockerfile`
4. Variables: ver [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md)
