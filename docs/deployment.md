# Guía de Despliegue On-Premise

> Instrucciones para desplegar la plataforma en un servidor interno con Docker Compose.
> Última actualización: 2026-06-04

---

## Requisitos del Servidor

| Recurso        | Mínimo                   | Recomendado                              |
| -------------- | ------------------------ | ---------------------------------------- |
| CPU            | 4 vCPU                   | 8 vCPU                                   |
| RAM            | 8 GB                     | 16 GB                                    |
| Disco          | 50 GB SSD                | 80 GB SSD + volumen adicional para datos |
| Docker Engine  | 24+                      | Última estable                           |
| Docker Compose | v2                       | Última estable                           |
| SO             | Ubuntu 22.04 / Debian 12 | Ubuntu 24.04                             |

---

## 1. Preparación del Servidor

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Verificar
docker --version
docker compose version

# Clonar repositorio
git clone <repo-url> /opt/evaluaciones-docentes
cd /opt/evaluaciones-docentes
```

---

## 2. Variables de Entorno

Crear `.env` en la raíz del proyecto. **No versionar este archivo.**

```bash
# ── Base de datos ────────────────────────────────
POSTGRES_DB=evaluaciones_docentes
POSTGRES_USER=eval_user
POSTGRES_PASSWORD=<contraseña-segura-generada>

# ── MinIO (almacenamiento S3) ───────────────────
MINIO_ROOT_USER=<usuario-seguro>
MINIO_ROOT_PASSWORD=<contraseña-segura-minio>
MINIO_BUCKET=evaluaciones

# ── Aplicación ──────────────────────────────────
SECRET_KEY=<openssl rand -hex 32>
ENVIRONMENT=production
ALLOWED_ORIGINS=https://evaluaciones.tudominio.local

# ── Gemini API (opcional, para consultas IA) ────
GEMINI_API_KEY=AIzaSy...tu-clave-real

# ── Puertos (ajustar si hay conflictos) ─────────
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

Generar secretos seguros:

```bash
openssl rand -hex 32  # Para SECRET_KEY
openssl rand -hex 16  # Para POSTGRES_PASSWORD
```

---

## 3. Despliegue

### 3.1 Construcción e inicio

```bash
# Construir y levantar todos los servicios
docker compose -f infra/docker/docker-compose.yml up -d --build

# Verificar estado
docker compose -f infra/docker/docker-compose.yml ps
```

### 3.2 Migraciones de base de datos

```bash
docker compose -f infra/docker/docker-compose.yml exec backend \
  alembic -c app/infrastructure/database/migrations/alembic.ini upgrade head
```

### 3.3 Verificación

```bash
# Health check del backend
curl http://localhost:8000/health

# Verificar que el frontend responde
curl -I http://localhost:3000

# Verificar PostgreSQL
docker compose -f infra/docker/docker-compose.yml exec postgres \
  pg_isready -U eval_user -d evaluaciones_docentes
```

### 3.4 Worker de Celery (opcional)

Solo necesario si se requiere procesamiento asíncrono de PDFs:

```bash
docker compose -f infra/docker/docker-compose.yml --profile worker up -d
```

---

## 4. Servicios Docker

| Servicio        | Imagen                         | Puerto     | Descripción                       |
| --------------- | ------------------------------ | ---------- | --------------------------------- |
| `postgres`      | `pgvector/pgvector:pg16`       | 5432       | PostgreSQL + pgvector             |
| `redis`         | `redis:7-alpine`               | 6379       | Broker Celery + caché             |
| `minio`         | `minio/minio:latest`           | 9000, 9001 | Almacenamiento S3 (API + consola) |
| `minio-init`    | `minio/mc:latest`              | —          | Bootstrap: crea bucket inicial    |
| `backend`       | Build local                    | 8000       | FastAPI (non-root: `appuser`)     |
| `celery-worker` | Build local (profile `worker`) | —          | Procesamiento asíncrono           |
| `frontend`      | Build local                    | 3000       | Next.js                           |

### Volúmenes persistentes

| Volumen         | Datos                      |
| --------------- | -------------------------- |
| `postgres_data` | Base de datos PostgreSQL   |
| `redis_data`    | Datos persistidos de Redis |
| `minio_data`    | PDFs almacenados           |

---

## 5. Nginx (Proxy Reverso)

### Configuración básica incluida

```nginx
# infra/docker/nginx/nginx.conf
upstream backend  { server backend:8000; }
upstream frontend { server frontend:3000; }

server {
    listen 80;
    client_max_body_size 50M;

    location /api/  { proxy_pass http://backend; ... }
    location /health { proxy_pass http://backend; }
    location /      { proxy_pass http://frontend; ... }
}
```

### TLS/SSL (producción)

Agregar certificados y configurar HTTPS:

```nginx
server {
    listen 443 ssl;
    server_name evaluaciones.tudominio.local;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # ... mismas locations que arriba
}

server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

Montar certificados como volumen en `docker-compose.yml`:

```yaml
nginx:
  volumes:
    - ./ssl:/etc/nginx/ssl:ro
```

### Seguridad del backend

El backend incluye middleware de seguridad automático:

- **Headers de seguridad:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- **En producción (`ENVIRONMENT=production`):** `Strict-Transport-Security: max-age=31536000` y `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`
- **Contenedor non-root:** El Dockerfile crea un usuario `appuser` — la aplicación nunca ejecuta como root
- **Rate limiting:** El endpoint `/api/v1/query` tiene límite de 10 requests/minuto por IP (Redis con fallback in-memory)
- **Validación de producción:** `config.py` valida que `SECRET_KEY` y `minio_secret_key` no tengan valores por defecto en producción

---

## 6. Backups

### PostgreSQL

```bash
# Backup completo
docker compose -f infra/docker/docker-compose.yml exec postgres \
  pg_dump -U eval_user evaluaciones_docentes > backup_$(date +%Y%m%d).sql

# Restaurar
cat backup_20260404.sql | docker compose -f infra/docker/docker-compose.yml exec -T postgres \
  psql -U eval_user -d evaluaciones_docentes
```

### Automatizar con cron

```bash
# /etc/cron.d/evaluaciones-backup
0 2 * * * root docker compose -f /opt/evaluaciones-docentes/infra/docker/docker-compose.yml exec -T postgres pg_dump -U eval_user evaluaciones_docentes | gzip > /opt/backups/db_$(date +\%Y\%m\%d).sql.gz
```

### MinIO

Los PDFs están en el volumen Docker `minio_data`. Respaldo:

```bash
# Copiar volumen
docker run --rm -v evaluaciones_minio_data:/data -v /opt/backups:/backup alpine \
  tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data
```

---

## 7. Actualización

```bash
cd /opt/evaluaciones-docentes

# Obtener cambios
git pull origin main

# Reconstruir y reiniciar
docker compose -f infra/docker/docker-compose.yml up -d --build

# Aplicar migraciones pendientes
docker compose -f infra/docker/docker-compose.yml exec backend \
  alembic -c app/infrastructure/database/migrations/alembic.ini upgrade head
```

---

## 8. Monitoreo

### Health checks

Docker Compose incluye health checks para `postgres`, `redis` y `minio`. Los servicios dependientes (`backend`, `celery-worker`) esperan a que las dependencias estén healthy.

### Logs

```bash
# Todos los servicios
docker compose -f infra/docker/docker-compose.yml logs -f

# Solo backend
docker compose -f infra/docker/docker-compose.yml logs -f backend

# Últimas 100 líneas
docker compose -f infra/docker/docker-compose.yml logs --tail=100 backend
```

### Métricas de PostgreSQL

```bash
docker compose -f infra/docker/docker-compose.yml exec postgres \
  psql -U eval_user -d evaluaciones_docentes \
  -c "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"
```

---

## 9. Troubleshooting

### El backend no inicia

```bash
# Ver logs detallados
docker compose -f infra/docker/docker-compose.yml logs backend

# Verificar que PostgreSQL está listo
docker compose -f infra/docker/docker-compose.yml exec postgres pg_isready
```

### Error de conexión a la base de datos

Verificar que `DATABASE_URL` en el backend coincide con las variables de PostgreSQL:

```
postgresql+asyncpg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@postgres:5432/<POSTGRES_DB>
```

### MinIO no crea el bucket

El contenedor `minio-init` crea el bucket automáticamente. Si falla:

```bash
docker compose -f infra/docker/docker-compose.yml up minio-init
```

### Disco lleno

```bash
# Ver uso de volúmenes Docker
docker system df -v

# Limpiar imágenes no usadas
docker image prune -af
```
