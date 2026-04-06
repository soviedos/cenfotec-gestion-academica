# Guía de Desarrollo Local

> Configuración del entorno de desarrollo sin Docker para backend y frontend.

Última actualización: 2026-06-04

---

## Prerrequisitos

| Herramienta | Versión mínima | Verificar             |
| ----------- | -------------- | --------------------- |
| Python      | 3.12           | `python3 --version`   |
| Node.js     | 20             | `node --version`      |
| PostgreSQL  | 16             | `psql --version`      |
| Redis       | 7              | `redis-cli --version` |
| MinIO       | latest         | `minio --version`     |
| Make        | any            | `make --version`      |

### macOS (Homebrew)

```bash
brew install python@3.12 node postgresql@16 redis minio/stable/minio
brew services start postgresql@16
brew services start redis
```

---

## 1. Variables de Entorno

```bash
# Desde la raíz del proyecto
make setup
```

Esto crea `.env`, `backend/.env` y `frontend/.env.local` a partir de los `.example`. Editar `backend/.env`:

```bash
# Obligatorio para consultas IA
GEMINI_API_KEY=AIzaSy...tu-clave-real

# Los demás valores por defecto funcionan para desarrollo local
DATABASE_URL=postgresql+asyncpg://eval_user:eval_pass_dev@localhost:5432/evaluaciones_docentes
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
```

---

## 2. Base de Datos

```bash
# Crear usuario y base de datos
psql postgres -c "CREATE USER eval_user WITH PASSWORD 'eval_pass_dev';"
psql postgres -c "CREATE DATABASE evaluaciones_docentes OWNER eval_user;"
psql evaluaciones_docentes -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql evaluaciones_docentes -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

---

## 3. MinIO (Almacenamiento de objetos)

```bash
# Iniciar MinIO en segundo plano
MINIO_ROOT_USER=minio_admin MINIO_ROOT_PASSWORD=minio_pass_dev \
  minio server /tmp/minio-data --address :9000 --console-address :9001 &

# Crear bucket (usando mc CLI)
mc alias set local http://localhost:9000 minio_admin minio_pass_dev
mc mb --ignore-existing local/evaluaciones
```

Consola web disponible en: http://localhost:9001

---

## 4. Backend (FastAPI)

```bash
cd backend

# Crear y activar entorno virtual
python3.12 -m venv .venv
source .venv/bin/activate

# Instalar dependencias (incluye dev)
pip install -e ".[dev]"

# Ejecutar migraciones
alembic -c app/infrastructure/database/migrations/alembic.ini upgrade head

# Iniciar servidor con hot-reload
uvicorn app.main:app --reload --port 8000
```

Endpoints disponibles:

- API: http://localhost:8000/api/v1/
- Docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health

### Celery Worker (opcional)

Solo necesario para procesamiento asíncrono de PDFs:

```bash
cd backend
source .venv/bin/activate
celery -A app.infrastructure.tasks.celery_app worker --loglevel=debug
```

---

## 5. Frontend (Next.js)

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

Disponible en: http://localhost:3000

El frontend usa un proxy reverso en `next.config.ts` que redirige `/api/*` al backend en `http://127.0.0.1:8000`, por lo que no se necesita configurar CORS manualmente.

---

## 6. Ejecutar Tests

### Backend

```bash
cd backend
source .venv/bin/activate

# Todos los tests
pytest tests/ -v

# Solo unit tests
pytest tests/unit/ -v

# Solo integration (requiere DB)
pytest tests/integration/ -v

# Solo API tests
pytest tests/api/ -v

# Con cobertura
pytest tests/ --cov=app --cov-report=html
```

### Frontend

```bash
cd frontend

# Todos los tests
npm test

# Con interfaz visual
npm run test:ui

# Con cobertura
npm run test:coverage

# E2E (requiere backend + frontend corriendo)
npm run test:e2e
```

### Desde la raíz (Make)

```bash
make test         # Backend + frontend
make test-back    # Solo backend
make test-front   # Solo frontend
make test-e2e     # E2E con Playwright
```

---

## 7. Linting

```bash
make lint         # Backend (ruff) + frontend (eslint)
make lint-back    # Solo backend
make lint-front   # Solo frontend
```

---

## 8. Migraciones de Base de Datos

```bash
# Aplicar todas las migraciones pendientes
make migrate

# Crear nueva migración (autogenerate desde modelos)
make migration
# → Se solicita nombre interactivamente

# Manualmente
cd backend
alembic -c app/infrastructure/database/migrations/alembic.ini upgrade head
alembic -c app/infrastructure/database/migrations/alembic.ini revision --autogenerate -m "descripcion"
```

---

## 9. Estructura de Comandos Rápida

| Acción                                 | Comando                                                                       |
| -------------------------------------- | ----------------------------------------------------------------------------- |
| Levantar solo infra (DB, Redis, MinIO) | `make infra`                                                                  |
| Detener infra                          | `make infra-down`                                                             |
| Backend local                          | `cd backend && uvicorn app.main:app --reload --port 8000`                     |
| Frontend local                         | `cd frontend && npm run dev`                                                  |
| Celery worker                          | `cd backend && celery -A app.infrastructure.tasks.celery_app worker -l debug` |
| Tests completos                        | `make test`                                                                   |
| Limpiar caches                         | `make clean`                                                                  |

---

## 10. Troubleshooting

### Error: `relation "..." does not exist`

Las migraciones no se han aplicado:

```bash
make migrate
```

### Error: `GEMINI_API_KEY no configurada` (503)

Editar `backend/.env` y agregar una clave válida de [Google AI Studio](https://aistudio.google.com/apikey).

### Error: `This model is no longer available` (404 de Gemini)

El modelo configurado fue deprecado. Verificar `_DEFAULT_MODEL` en `backend/app/infrastructure/external/gemini_gateway.py`.

### Frontend no conecta al backend

Verificar que el backend esté corriendo en el puerto 8000. Next.js redirige `/api/*` via `rewrites` en `next.config.ts`.

### Puerto ocupado

```bash
lsof -i :8000  # ¿Quién usa el puerto?
kill -9 <PID>  # Liberar
```
