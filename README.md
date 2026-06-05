# DTS Backend

API Django + portales web. Parte del monorepo [DTS-E-Commerce](../README.md).

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
