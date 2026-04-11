# Backend — Evaluaciones Docentes

> API REST construida con FastAPI y Python 3.12, con procesamiento asíncrono vía BackgroundTasks y análisis con Gemini API.

---

## Stack

| Tecnología                                       | Uso                                        |
| ------------------------------------------------ | ------------------------------------------ |
| [FastAPI](https://fastapi.tiangolo.com/)         | Framework web async con OpenAPI automático |
| [SQLAlchemy 2.0](https://www.sqlalchemy.org/)    | ORM con soporte async                      |
| [Alembic](https://alembic.sqlalchemy.org/)       | Migraciones de base de datos               |
| [Pydantic v2](https://docs.pydantic.dev/)        | Validación de datos y settings             |
| [Redis](https://redis.io/)                       | Cache y rate-limiting                      |
| [MinIO](https://min.io/)                         | Almacenamiento de objetos (PDFs)           |
| [pgvector](https://github.com/pgvector/pgvector) | Embeddings y búsqueda semántica            |
| [PyMuPDF](https://pymupdf.readthedocs.io/)       | Extracción de texto de PDFs                |
| [Gemini API](https://ai.google.dev/)             | Análisis con IA generativa                 |

---

## Estructura de Carpetas

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      → Punto de entrada FastAPI
│   ├── core/
│   │   ├── config.py                → Settings con pydantic-settings
│   │   ├── cache.py                 → Caché y rate limiting
│   │   └── logging.py               → Configuración de logging
│   ├── api/
│   │   ├── deps.py                  → Dependencias inyectables (DB session, repos)
│   │   ├── rate_limit.py            → Rate limiter para endpoints
│   │   └── v1/
│   │       ├── router.py            → Agregador de routers v1
│   │       ├── evaluaciones.py      → CRUD de evaluaciones
│   │       ├── documentos.py        → Upload y gestión de PDFs
│   │       ├── config_routes.py     → Endpoint de configuración (umbrales)
│   │       └── ...                  → analytics, qualitative, query, etc.
│   ├── domain/                      → Lógica de negocio pura
│   │   ├── alert_rules.py           → Reglas y umbrales de alertas
│   │   ├── periodo.py               → Parsing y ordenamiento temporal
│   │   ├── entities/                → Entidades del dominio (SQLAlchemy)
│   │   └── schemas/                 → Schemas Pydantic (request/response)
│   ├── application/                 → Servicios de aplicación
│   │   ├── services/                → Orquestadores de negocio
│   │   ├── parsing/                 → Extracción de texto de PDFs
│   │   └── classification/          → Clasificación de comentarios
│   ├── infrastructure/              → Adaptadores externos
│   │   ├── external/
│   │   │   └── gemini_gateway.py    → Wrapper Gemini con retry + circuit breaker
│   │   ├── repositories/            → Repositorios (PostgreSQL)
│   │   ├── storage/                 → MinIO client
│   │   └── tasks/                   → Celery (reservado para migración futura)
├── scripts/                         → Scripts operacionales (backfill, reanalyze)
├── tests/
│   ├── conftest.py                  → Fixtures compartidos (TestClient, DB)
│   ├── unit/                        → Tests unitarios
│   ├── integration/                 → Tests de integración
│   └── fixtures/                    → PDFs de prueba y datos mock
├── pyproject.toml                   → Dependencias y configuración de herramientas
├── Dockerfile
└── .env.example
```

---

## Desarrollo Local

### Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

### Instalación

```bash
cd backend

# Crear entorno virtual e instalar dependencias
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Copiar variables de entorno
cp .env.example .env

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`.  
Documentación interactiva en `http://localhost:8000/docs`.

### Variables de Entorno

| Variable           | Descripción                     | Ejemplo                                                      |
| ------------------ | ------------------------------- | ------------------------------------------------------------ |
| `DATABASE_URL`     | Cadena de conexión a PostgreSQL | `postgresql+asyncpg://user:pass@localhost:5432/evaluaciones` |
| `REDIS_URL`        | URL del broker Redis            | `redis://localhost:6379/0`                                   |
| `MINIO_ENDPOINT`   | Host y puerto de MinIO          | `localhost:9000`                                             |
| `MINIO_ACCESS_KEY` | Clave de acceso MinIO           | `minioadmin`                                                 |
| `MINIO_SECRET_KEY` | Clave secreta MinIO             | `minioadmin`                                                 |
| `GEMINI_API_KEY`   | API key de Google Gemini        | `AIza...`                                                    |

---

## Scripts y Comandos

```bash
# Servidor de desarrollo
uvicorn app.main:app --reload --port 8000

# Ejecutar tests
pytest

# Tests con cobertura
pytest --cov=app --cov-report=html

# Lint
ruff check .

# Formato automático
ruff format .

# Crear migración
alembic -c app/db/migrations/alembic.ini revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic -c app/db/migrations/alembic.ini upgrade head

# Iniciar worker Celery (opcional, no requerido en modo BackgroundTasks)
# celery -A app.infrastructure.tasks.celery_app worker --loglevel=info
```

---

## Convenciones

- **Archivos**: `snake_case` (`pdf_parser.py`, `gemini_analyzer.py`)
- **Clases**: `PascalCase` (`Evaluacion`, `DocumentoCreate`)
- **Endpoints**: `kebab-case` plural (`/api/v1/evaluaciones`)
- **Modelos SQLAlchemy**: singular (`Evaluacion`), tabla plural (`evaluaciones`)
- **Schemas Pydantic**: sufijo según uso (`EvaluacionCreate`, `EvaluacionResponse`)
- **Services**: lógica de negocio pura, sin dependencia de FastAPI
- **Tasks**: solo orquestación; delegan al service correspondiente

---

## Versionado de API

La API se versiona con prefijo en la URL: `/api/v1/`. Cuando se requiera un cambio incompatible, se creará `/api/v2/` sin remover la versión anterior hasta que todos los clientes migren.
