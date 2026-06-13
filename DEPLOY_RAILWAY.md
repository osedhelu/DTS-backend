# Despliegue en Railway — submódulo backend

Este repo (`backend/`) se despliega **solo**, sin el monorepo padre.

## Configuración en Railway

| Campo | Valor |
|-------|--------|
| **Repositorio** | Repo del submódulo `backend` (no el monorepo) |
| **Root Directory** | `/` (raíz del repo backend) |
| **Builder** | Dockerfile (detectado vía `railway.toml`) |
| **Dockerfile** | `Dockerfile` |

> **No uses Railpack/Nixpacks** — PostGIS requiere GDAL en la imagen Docker.

## Variables de entorno (DTS-backend)

```env
SECRET_KEY=<clave-larga-aleatoria>
DEBUG=False
ALLOWED_HOSTS=.up.railway.app,tu-servicio.up.railway.app
CSRF_TRUSTED_ORIGINS=https://tu-servicio.up.railway.app

DATABASE_URL=${{postgis.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

RUN_MIGRATIONS=true
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120

SERVE_MEDIA=True
MEDIA_PUBLIC_BASE_URL=https://tu-servicio.up.railway.app
MEDIA_ROOT=/app/media

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailpit.railway.internal
EMAIL_PORT=1025
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@dts.local
```

Genera dominio público en **Networking** y actualiza `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y `MEDIA_PUBLIC_BASE_URL`.

## Volumen persistente para imágenes (MEDIA)

Sin volumen, las fotos de producto/logos **se pierden** en cada redeploy.

| Campo | Valor |
|-------|--------|
| **Nombre volumen** | `dts-media` |
| **Mount path** | `/app/media` |
| **Variable** | `MEDIA_ROOT=/app/media` |

Railway expone automáticamente `RAILWAY_VOLUME_MOUNT_PATH` al montar el volumen.

**Crear vía CLI** (desde repo backend, con `railway link`):

```bash
railway volume add --mount-path /app/media
```

**Crear vía dashboard:** DTS-backend → Settings → Volumes → Add Volume → mount `/app/media`

Tras crear el volumen, **redeploy** el servicio para activarlo.

> Producción a largo plazo: considera S3 (`MEDIA_STORAGE_BACKEND=s3`). Ver [MEDIA_STORAGE.md](../docs/MEDIA_STORAGE.md) en el monorepo.

## Variables corregidas (referencia Railway)

```env
SECRET_KEY=<clave-larga-aleatoria>
DEBUG=False

ALLOWED_HOSTS=localhost,127.0.0.1,healthcheck.railway.app,${{RAILWAY_PUBLIC_DOMAIN}}
CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}

DATABASE_URL=${{postgis.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

RUN_MIGRATIONS=true
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120

SERVE_MEDIA=True
MEDIA_PUBLIC_BASE_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
MEDIA_ROOT=/app/media

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=${{Mailpit.RAILWAY_PRIVATE_DOMAIN}}
EMAIL_PORT=1025
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@dts.local
```

No uses comillas en los valores del dashboard Railway.

## Celery (servicios extra, mismo repo)

**Worker:**

```bash
uv run celery -A core worker --loglevel=info --concurrency=2
```

**Beat:**

```bash
uv run celery -A core beat --loglevel=info --schedule /tmp/celerybeat-schedule
```

Mismas variables que la API. Sin networking público.

## Superusuario

```bash
railway login
railway link
railway service DTS-backend
railway run uv run python manage.py createsuperuser
```

## Verificar

```bash
curl https://tu-servicio.up.railway.app/api/v1/docs/
```

## Troubleshooting

| Error | Solución |
|-------|----------|
| `Could not find the GDAL library` | Builder = Dockerfile, no Railpack |
| Root Directory = subcarpeta incorrecta | Debe ser `/` (raíz del repo backend) |
| `DisallowedHost` / healthcheck | Añadir `healthcheck.railway.app` a `ALLOWED_HOSTS` |
| Imágenes se pierden al redeploy | Volumen en `/app/media` + `MEDIA_ROOT=/app/media` |
| DB connection failed | `DATABASE_URL=${{postgis.DATABASE_URL}}` |

## Desarrollo local con BD Railway

En `.env` usa la URL **TCP pública** de PostGIS (no `*.railway.internal`):

```env
DATABASE_URL=postgresql://postgres:PASS@HOST:PORT/ECOMMERCE_DIS
```
