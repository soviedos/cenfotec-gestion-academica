# Evaluaciones Docentes

> Plataforma web interna para el análisis automatizado de evaluaciones docentes a partir de documentos PDF, potenciada por inteligencia artificial.

---

## Descripción

**Evaluaciones Docentes** es un sistema institucional diseñado para recibir evaluaciones docentes en formato PDF, procesarlas de forma automática y extraer información estructurada mediante IA generativa (Gemini). Los resultados se almacenan en una base de datos relacional con soporte para búsqueda semántica, lo que permite generar reportes, visualizar tendencias y consultar evaluaciones de forma inteligente.

### Características principales

- Carga masiva de evaluaciones en formato PDF
- Extracción automática de texto y datos estructurados
- Análisis semántico con Gemini API
- Búsqueda por similitud mediante embeddings (pgvector)
- Dashboard de reportes y métricas por docente, periodo y facultad
- Procesamiento asíncrono en segundo plano (Celery)
- Arquitectura on-premise, sin dependencia de servicios cloud externos

---

## Stack Tecnológico

| Capa                      | Tecnología              | Versión mínima |
| ------------------------- | ----------------------- | -------------- |
| Frontend                  | Next.js + TypeScript    | 16.x           |
| Backend                   | FastAPI + Python        | 3.12           |
| Base de datos             | PostgreSQL + pgvector   | 16             |
| Cola de tareas            | Redis + Celery          | 7.x / 5.x      |
| Almacenamiento de objetos | MinIO                   | latest         |
| Inteligencia artificial   | Gemini API              | 2.x            |
| Contenedores              | Docker + Docker Compose | 24.x / 2.x     |
| Proxy reverso             | Nginx                   | 1.25           |

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

# 2. Copiar variables de entorno
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# 3. Levantar toda la stack con Docker Compose
make dev

# 4. Verificar que los servicios estén activos
#    Backend API:   http://localhost:8000/health
#    Frontend:      http://localhost:3000
#    MinIO Console: http://localhost:9001
#    API Docs:      http://localhost:8000/docs
```

---

## Comandos Principales

Todos los comandos se ejecutan desde la raíz del proyecto vía `Makefile`:

```bash
make dev          # Levantar todos los servicios en modo desarrollo
make down         # Detener y destruir todos los contenedores
make build        # Reconstruir imágenes Docker
make test         # Ejecutar todos los tests (backend + frontend)
make test-back    # Tests del backend (pytest)
make test-front   # Tests del frontend (vitest/jest)
make lint         # Lint de todo el proyecto (ruff + eslint)
make migrate      # Ejecutar migraciones de base de datos (Alembic)
make logs         # Ver logs en tiempo real de todos los servicios
```

---

## Estructura del Proyecto

```
Evaluaciones_Docentes/
├── frontend/             → Aplicación web (Next.js + TypeScript)
├── backend/              → API REST y lógica de negocio (FastAPI + Python)
├── infra/                → Docker Compose, Nginx, scripts de infraestructura
├── docs/                 → Documentación técnica del proyecto
├── .github/              → Workflows CI/CD y templates de PR/Issues
├── .vscode/              → Configuración compartida del editor
├── Makefile              → Comandos abreviados para desarrollo
├── .editorconfig         → Reglas de formato entre editores
├── .gitignore            → Archivos excluidos del control de versiones
└── LICENSE               → Licencia del proyecto
```

Cada subdirectorio contiene su propio `README.md` con documentación específica.

---

## Documentación

| Documento                                      | Descripción                                    |
| ---------------------------------------------- | ---------------------------------------------- |
| [docs/README.md](docs/README.md)               | Índice general de documentación                |
| [docs/architecture.md](docs/architecture.md)   | Arquitectura del sistema y decisiones técnicas |
| [docs/api-contracts.md](docs/api-contracts.md) | Contratos y especificación de la API REST      |
| [docs/deployment.md](docs/deployment.md)       | Guía de despliegue on-premise                  |
| [docs/adr/](docs/adr/)                         | Registros de decisiones arquitectónicas (ADR)  |

---

## Flujo de Trabajo con Git

Este proyecto sigue el flujo **Git Flow simplificado**:

| Rama      | Propósito                                 |
| --------- | ----------------------------------------- |
| `main`    | Código estable en producción              |
| `develop` | Integración de features terminadas        |
| `feat/*`  | Desarrollo de funcionalidades             |
| `fix/*`   | Corrección de errores                     |
| `chore/*` | Tareas de infraestructura o configuración |

Los commits siguen la convención [Conventional Commits](https://www.conventionalcommits.org/):

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
