# Despliegue en Railway — submódulo backend

Este repo (`backend/`) se despliega **solo**, sin el monorepo padre.

## Servicios Railway (mismo repo `osedhelu/DTS-backend`)

| Servicio | Config file | Dominio público | Rol |
|----------|-------------|-----------------|-----|
| **DTS-backend** | `railway.toml` | ✅ Sí | API Django (Gunicorn) |
| **DTS-celery-worker** | `railway.worker.toml` | ❌ No | Tareas async (email, push, pedidos…) |
| **DTS-celery-beat** | `railway.beat.toml` | ❌ No | Tareas programadas (stats 02:00) |

Todos usan el **mismo Dockerfile** y Root Directory `/`.

---

## 1. DTS-backend (API)

| Campo | Valor |
|-------|--------|
| **Repositorio** | `osedhelu/DTS-backend` |
| **Root Directory** | `/` |
| **Config file** | `/railway.toml` (default) |
| **Builder** | Dockerfile |

> **No uses Railpack/Nixpacks** — PostGIS requiere GDAL en la imagen Docker.

### Variables (DTS-backend)

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
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@dts.local

WEB_URL=https://${{DTS-web-admin.RAILWAY_PUBLIC_DOMAIN}}
```

Sin comillas en el dashboard Railway.

### Volumen MEDIA (DTS-backend)

| Campo | Valor |
|-------|--------|
| Nombre | `dts-media` |
| Mount path | `/app/media` |

```bash
railway volume add --mount-path /app/media   # con link a DTS-backend
```

---

## 2. DTS-celery-worker

### Crear servicio

1. Railway → **E commerce Disglobal** → **+ New** → **GitHub Repo**
2. Repo: **`osedhelu/DTS-backend`**
3. Nombre: **`DTS-celery-worker`**

### Settings

| Campo | Valor |
|-------|--------|
| Root Directory | `/` |
| **Config file path** | `/railway.worker.toml` |
| Public networking | **Off** (sin Generate Domain) |

El archivo `railway.worker.toml` define el start command y **no** incluye healthcheck HTTP.

### Variables (copiar de DTS-backend + estas)

```env
RUN_MIGRATIONS=false
CELERY_CONCURRENCY=2

SECRET_KEY=${{DTS-backend.SECRET_KEY}}
DEBUG=False

DATABASE_URL=${{postgis.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=${{Mailpit.RAILWAY_PRIVATE_DOMAIN}}
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@dts.local

WEB_URL=https://${{DTS-web-admin.RAILWAY_PUBLIC_DOMAIN}}
MEDIA_PUBLIC_BASE_URL=https://${{DTS-backend.RAILWAY_PUBLIC_DOMAIN}}
```

No necesita `ALLOWED_HOSTS` ni volumen `/app/media` (no sirve HTTP ni sube fotos).

### Verificar

```bash
cd backend
railway link -s DTS-celery-worker
railway logs
```

Esperado: `celery@... ready.`

---

## 3. DTS-celery-beat

### Crear servicio

1. **+ New** → **GitHub Repo** → `osedhelu/DTS-backend`
2. Nombre: **`DTS-celery-beat`**

### Settings

| Campo | Valor |
|-------|--------|
| Root Directory | `/` |
| **Config file path** | `/railway.beat.toml` |
| Public networking | **Off** |
| **Replicas** | **1** (nunca más de una instancia de beat) |

### Volumen opcional (persistir schedule)

| Campo | Valor |
|-------|--------|
| Mount path | `/tmp` |

### Variables

Las mismas que **DTS-celery-worker** (`RUN_MIGRATIONS=false`, etc.).

### Tarea programada

| Tarea | Horario |
|-------|---------|
| `calculate_daily_stats` | 02:00 (America/Bogota) |

### Verificar

```bash
railway link -s DTS-celery-beat
railway logs
```

Esperado: `beat: Starting...`

---

## 4. Probar Celery end-to-end

1. Worker y beat en **SUCCESS**
2. Registro en web-admin: `/registro-comercio`
3. El email debe aparecer en **Mailpit** (procesado por el worker)
4. Al cambiar estado de un pedido, el worker ejecuta asignación/notificaciones

---

## Superusuario

```bash
cd backend
railway link -s DTS-backend
railway ssh uv run python manage.py migrate
railway ssh uv run python manage.py createsuperuser
```

> `railway run` ejecuta en tu Mac (falla sin GDAL). Usa **`railway ssh`**.

---

## Verificar API

```bash
curl -I https://dts-backend-production-c84e.up.railway.app/api/v1/docs/
```

---

## Troubleshooting

| Error | Solución |
|-------|----------|
| Worker CRASHED / healthcheck | Config file debe ser `railway.worker.toml` (sin healthcheck HTTP) |
| `Could not find the GDAL library` | Builder = Dockerfile, no Railpack |
| `DisallowedHost` / healthcheck API | Añadir `healthcheck.railway.app` a `ALLOWED_HOSTS` |
| Emails no llegan | Worker corriendo + `REDIS_URL` + Mailpit SMTP |
| Beat duplicado | Solo 1 réplica de `DTS-celery-beat` |
| Migrate conflictos | `RUN_MIGRATIONS=false` en worker y beat |
| Links email a localhost | `WEB_URL` en DTS-backend apuntando al web-admin |

---

## Desarrollo local con BD Railway

En `.env` usa la URL **TCP pública** de PostGIS (no `*.railway.internal`):

```env
DATABASE_URL=postgresql://postgres:PASS@HOST:PORT/ECOMMERCE_DIS
```
