# Evaluaciones Docentes

> Plataforma web interna para el análisis automatizado de evaluaciones docentes a partir de documentos PDF, potenciada por inteligencia artificial.

---

## Descripción

**Evaluaciones Docentes** es un sistema institucional diseñado para recibir evaluaciones docentes en formato PDF, procesarlas de forma automática y extraer información estructurada. Los datos cuantitativos se extraen con un **parser determinístico** (PyMuPDF), mientras que los comentarios cualitativos se analizan con **Gemini API**. Los resultados se almacenan en PostgreSQL con soporte para búsqueda semántica (pgvector), lo que permite generar reportes, visualizar tendencias y consultar evaluaciones en lenguaje natural.

### Características principales

- **Carga de PDFs** con deduplicación SHA-256 y almacenamiento en MinIO
- **Parser determinístico** — extracción de encabezados, métricas por dimensión, cursos y comentarios
- **Clasificación cualitativa** — detección de tema, sentimiento y tipo (fortaleza/mejora/observación)
- **Consultas IA** — endpoint RAG que recupera métricas + comentarios y genera respuestas con Gemini
- **Dashboards interactivos** — estadísticos (KPIs, radar, tendencias) y de sentimiento (temas, distribución)
- **Auditoría completa** — cada llamada a Gemini se registra con prompt, tokens, latencia y resultado
- **Procesamiento asíncrono** en segundo plano (FastAPI BackgroundTasks; Celery disponible como perfil opcional)
- **Arquitectura on-premise**, sin dependencia de servicios cloud externos (excepto Gemini API)

---

## Stack Tecnológico

| Capa                    | Tecnología                | Versión    |
| ----------------------- | ------------------------- | ---------- |
| Frontend                | Next.js + TypeScript      | 16.x       |
| UI Components           | shadcn/ui + Tailwind v4   | 4.x        |
| Gráficos                | Recharts                  | 3.x        |
| Backend                 | FastAPI + Python          | 3.12       |
| ORM                     | SQLAlchemy 2.0 (async)    | 2.x        |
| Base de datos           | PostgreSQL + pgvector     | 16         |
| Cola de tareas          | FastAPI BackgroundTasks   | —          |
| Cache / Rate-limit      | Redis                     | 7.x        |
| Almacenamiento objetos  | MinIO                     | latest     |
| Inteligencia artificial | Gemini API (google-genai) | 2.5-flash  |
| Contenedores            | Docker + Docker Compose   | 24.x / 2.x |
| Proxy reverso           | Nginx                     | 1.25       |

---

## Requisitos Previos

- **Docker** y **Docker Compose** v2+
- **Node.js** 20+ (desarrollo local del frontend)
- **Python** 3.12+ (desarrollo local del backend)
- **Make** (para comandos abreviados)
- **Git** 2.40+

---

## Inicio Rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/soviedos/Evaluaciones_Docentes.git
cd Evaluaciones_Docentes

# 2. Configurar variables de entorno
make setup
# Luego editar backend/.env y agregar GEMINI_API_KEY

# 3. Levantar toda la stack con Docker Compose
make dev

# 4. Ejecutar migraciones
make migrate

# 5. Verificar que los servicios estén activos
#    Backend API:   http://localhost:8000/health
#    Frontend:      http://localhost:3000
#    MinIO Console: http://localhost:9001
#    API Docs:      http://localhost:8000/docs
```

Para desarrollo local sin Docker, ver [docs/local-development.md](docs/local-development.md).

---

## Comandos Principales

```bash
make dev          # Levantar todos los servicios en modo desarrollo
make dev-worker   # Todo + Celery worker (perfil opcional)
make infra        # Solo infraestructura (postgres, redis, minio)
make down         # Detener contenedores
make down-clean   # Detener + eliminar volúmenes (¡destructivo!)
make build        # Reconstruir imágenes Docker
make test         # Ejecutar todos los tests (backend + frontend)
make test-back    # Tests del backend (pytest)
make test-front   # Tests del frontend (vitest)
make test-e2e     # Tests E2E (playwright)
make lint         # Lint de todo el proyecto (ruff + eslint)
make migrate      # Ejecutar migraciones de base de datos
make migration    # Crear nueva migración con autogenerate
make logs         # Ver logs en tiempo real
make ps           # Ver estado de servicios
make clean        # Limpiar caches y artefactos
```

---

## Estructura del Proyecto

```
Evaluaciones_Docentes/
├── frontend/             → Aplicación web (Next.js 16 + TypeScript)
│   ├── src/app/          → Páginas (App Router con route groups)
│   ├── src/components/   → Componentes React por dominio
│   ├── src/hooks/        → Custom hooks (data fetching)
│   ├── src/lib/          → API client, utilidades
│   ├── src/types/        → Interfaces TypeScript
│   ├── tests/            → Unit + component tests (Vitest)
│   └── e2e/              → Tests E2E (Playwright)
├── backend/              → API REST (FastAPI + Python 3.12)
│   ├── app/api/          → Endpoints y dependencias
│   ├── app/application/  → Servicios, parsing, clasificación
│   ├── app/core/         → Config, logging
│   ├── app/domain/       → Entidades, schemas, excepciones
│   ├── app/infrastructure/ → DB, storage, Gemini, tasks
│   └── tests/            → Unit, integration, API tests (pytest)
├── infra/                → Docker Compose, Nginx, scripts
├── docs/                 → Documentación técnica
├── Makefile              → Comandos abreviados
└── LICENSE               → MIT
```

---

## Documentación

| Documento                                                  | Descripción                                        |
| ---------------------------------------------------------- | -------------------------------------------------- |
| [docs/architecture.md](docs/architecture.md)               | Arquitectura del sistema y diagrama de componentes |
| [docs/local-development.md](docs/local-development.md)     | Guía completa de desarrollo local                  |
| [docs/data-model.md](docs/data-model.md)                   | Modelo de datos y diagrama ER                      |
| [docs/processing-pipeline.md](docs/processing-pipeline.md) | Flujo de procesamiento documental                  |
| [docs/testing-strategy.md](docs/testing-strategy.md)       | Estrategia y convenciones de testing               |
| [docs/deployment.md](docs/deployment.md)                   | Guía de despliegue on-premise                      |
| [docs/gemini-integration.md](docs/gemini-integration.md)   | Guía de integración con Gemini API                 |
| [docs/api-contracts.md](docs/api-contracts.md)             | Contratos de la API REST                           |
| [docs/adr/](docs/adr/)                                     | Registros de decisiones arquitectónicas            |

---

## Flujo de Trabajo con Git

| Rama      | Propósito                                 |
| --------- | ----------------------------------------- |
| `main`    | Código estable en producción              |
| `develop` | Integración de features terminadas        |
| `feat/*`  | Desarrollo de funcionalidades             |
| `fix/*`   | Corrección de errores                     |
| `chore/*` | Tareas de infraestructura o configuración |

Commits siguen [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(backend): add PDF upload endpoint
fix(frontend): correct date format in report view
chore(infra): update PostgreSQL version in compose
```

---

## Contribución

1. Crear una rama desde `develop`: `git checkout -b feat/mi-feature`
2. Desarrollar y hacer commits siguiendo Conventional Commits
3. Abrir un Pull Request hacia `develop`
4. Esperar revisión y aprobación
5. Merge vía squash merge

---

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.
