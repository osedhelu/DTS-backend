# DTS Backend

API REST Django (DRF). Parte del monorepo [DTS-E-Commerce](../README.md).

El frontend administrativo vive en `web-admin/` (Next.js), no en este proyecto.

## Setup

```bash
cp .env.example .env
uv sync
```

Requiere PostGIS y Redis (`make docker-up` desde la raíz).

## Comandos

```bash
make test       # pytest
make migrate    # migraciones
make run        # runserver :8000
```
