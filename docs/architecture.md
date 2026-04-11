# Arquitectura del Sistema

> Documento técnico de arquitectura para la plataforma **Evaluaciones Docentes**.
> Última actualización: 2026-06-04

---

## Índice

1. [Visión general](#1-visión-general)
2. [Arquitectura lógica](#2-arquitectura-lógica)
3. [Responsabilidades por capa](#3-responsabilidades-por-capa)
4. [Flujo completo: del PDF a la consulta IA](#4-flujo-completo-del-pdf-a-la-consulta-ia)
5. [Módulos principales](#5-módulos-principales)
6. [Decisiones técnicas clave](#6-decisiones-técnicas-clave)
7. [Riesgos y mitigaciones](#7-riesgos-y-mitigaciones)
8. [Infraestructura on-premise](#8-infraestructura-on-premise)

### Documentos relacionados

| Tema                      | Documento                                        |
| ------------------------- | ------------------------------------------------ |
| Modelo de datos           | [data-model.md](data-model.md)                   |
| Pipeline de procesamiento | [processing-pipeline.md](processing-pipeline.md) |
| Integración con Gemini    | [gemini-integration.md](gemini-integration.md)   |
| Estrategia de testing     | [testing-strategy.md](testing-strategy.md)       |
| Despliegue on-premise     | [deployment.md](deployment.md)                   |
| Desarrollo local          | [local-development.md](local-development.md)     |
| Contratos de API          | [api-contracts.md](api-contracts.md)             |

---

## 1. Visión General

El sistema recibe evaluaciones docentes en formato PDF (documentos homogéneos con estructura conocida), extrae su contenido, lo analiza mediante inteligencia artificial generativa y almacena los resultados de forma estructurada para consulta, búsqueda semántica y generación de reportes.

**Principios de diseño:**

- **Procesamiento desacoplado**: la carga de PDFs y su análisis son operaciones independientes y asíncronas
- **Datos primero**: toda información extraída se persiste de forma estructurada antes de visualizarse
- **On-premise**: ningún dato institucional transita por servicios cloud, excepto las llamadas a Gemini API (solo texto extraído, nunca el PDF original)
- **Extensibilidad**: nuevos tipos de análisis o formatos de PDF se agregan sin modificar el flujo existente

---

## 2. Arquitectura Lógica

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            RED INTERNA (Proxmox)                        │
│                                                                         │
│  ┌───────────┐     ┌──────────────┐     ┌──────────────────────────┐   │
│  │  Browser   │────▶│    Nginx     │────▶│       Next.js            │   │
│  │  (MPA)     │◀────│   :80/:443   │◀────│    Frontend :3000        │   │
│  └───────────┘     └──────────────┘     └────────────┬─────────────┘   │
│                                                      │ fetch /api/v1   │
│                                                      ▼                 │
│                                          ┌──────────────────────┐      │
│                                          │      FastAPI         │      │
│                                          │    Backend :8000     │      │
│                                          └─┬────┬────┬────┬────┘      │
│                                            │    │    │    │            │
│                     ┌──────────────────────┘    │    │    └──────┐     │
│                     ▼                           ▼    ▼          ▼     │
│                                      │   Redis    │  ┌────────────┐   │
│              ┌─────────────┐          │   :6379    │  │   MinIO    │   │
│              │ PostgreSQL  │          │   :6379    │  │ :9000/:9001│   │
│              │ + pgvector  │          └───────────┘  └────────────┘   │
│              │    :5432    │                                         │
│              └─────────────┘                                         │
│                                                                    │
└────────────────────────────────────────────────┬───────────────────┘
                                              │ HTTPS (solo texto)
                                       ┌──────▼──────┐
                                       │  Gemini API │
                                       │  (externo)  │
                                       └─────────────┘
```

### Capas del sistema

| Capa               | Componente            | Responsabilidad principal                              |
| ------------------ | --------------------- | ------------------------------------------------------ |
| **Presentación**   | Next.js (App Router)  | Renderizado de páginas, interacción con el usuario     |
| **Proxy**          | Nginx                 | Terminación TLS, enrutamiento, rate limiting           |
| **API**            | FastAPI               | Validación, autenticación, orquestación de servicios   |
| **Dominio**        | Services (Python)     | Lógica de negocio pura: parseo, análisis, reportes     |
| **Procesamiento**  | BackgroundTasks       | Ejecución asíncrona de tareas de procesamiento de PDFs |
| **Persistencia**   | PostgreSQL + pgvector | Datos estructurados + embeddings vectoriales           |
| **Almacenamiento** | MinIO                 | Archivos binarios (PDFs originales)                    |
| **Mensajería**     | Redis                 | Caché ligero + rate limiter                            |
| **IA externa**     | Gemini API            | Análisis semántico y generación de embeddings          |

---

## 3. Responsabilidades por Capa

### 3.1 Capa de Presentación (Next.js)

| Responsabilidad         | Detalle                                                                |
| ----------------------- | ---------------------------------------------------------------------- |
| Renderizado MPA         | Cada sección es una página independiente con su propia ruta. No es SPA |
| Upload de archivos      | Formulario de carga de PDFs con validación client-side (tipo, tamaño)  |
| Consulta de datos       | Fetch al backend API para listar evaluaciones, reportes, búsquedas     |
| Visualización           | Tablas, gráficas, detalle de evaluación individual                     |
| Estado de procesamiento | Polling o notificación del estado de tareas asíncronas                 |

**No hace:** lógica de negocio, acceso directo a base de datos, procesamiento de PDFs.

### 3.2 Capa de API (FastAPI)

| Responsabilidad            | Detalle                                                   |
| -------------------------- | --------------------------------------------------------- |
| Validación de entrada      | Schemas Pydantic validan todo request antes de procesarlo |
| Autenticación/Autorización | Middleware JWT o session-based para usuarios internos     |
| Orquestación               | Recibe requests, delega al service o lanza BackgroundTask |
| Serialización de respuesta | Schemas de salida garantizan formato consistente          |
| Documentación automática   | OpenAPI/Swagger generado automáticamente                  |

**No hace:** transformación de datos compleja, acceso directo a Gemini, almacenamiento de archivos.

### 3.3 Capa de Dominio (Services)

| Responsabilidad             | Detalle                                                            |
| --------------------------- | ------------------------------------------------------------------ |
| `processing_service`        | Pipeline completo: parseo → clasificación → persistencia           |
| `document_service`          | CRUD de documentos, deduplicación, eliminación con MinIO           |
| `analytics_service`         | Métricas agregadas: dimensiones, docentes, evolución, ranking      |
| `qualitative_service`       | Comentarios clasificados, distribuciones, nube de palabras         |
| `query_service`             | Orquestador RAG: retrieval SQL → Gemini → auditoría                |
| `alert_engine`              | Motor de reglas de negocio para generación automática de alertas   |
| `alerta_service`            | CRUD y gestión de estado de alertas                                |
| `dashboard_service`         | Agregaciones para dashboard ejecutivo (KPIs, tendencias, insights) |
| `gemini_enrichment_service` | Enriquecimiento de comentarios con Gemini (clasificación avanzada) |

**Principio:** los servicios son clases sin dependencia de FastAPI. Reciben repositorios por inyección de dependencias. Se invocan desde endpoints y desde BackgroundTasks indistintamente.

### 3.4 Capa de Procesamiento (BackgroundTasks)

| Responsabilidad         | Detalle                                                            |
| ----------------------- | ------------------------------------------------------------------ |
| Procesamiento asíncrono | Desacopla la carga del PDF de su análisis                          |
| Pipeline secuencial     | `upload → parseo → clasificación → enriquecimiento → persistencia` |
| Manejo de errores       | Fallos marcan `documentos.estado = 'error'`                        |

### 3.5 Capa de Persistencia (PostgreSQL + pgvector)

| Tabla                      | Propósito                                                      |
| -------------------------- | -------------------------------------------------------------- |
| `documentos`               | Metadatos del PDF (nombre, hash SHA-256, ruta MinIO, estado)   |
| `evaluaciones`             | Datos estructurados extraídos de cada evaluación               |
| `evaluacion_dimensiones`   | Puntajes por dimensión pedagógica (METODOLOGÍA, Dominio, etc.) |
| `evaluacion_cursos`        | Datos por curso-grupo (respondieron, matriculados, %)          |
| `comentario_analisis`      | Comentarios clasificados (tema, sentimiento, fuente)           |
| `gemini_audit_log`         | Auditoría de cada llamada a Gemini API                         |
| `alertas`                  | Alertas generadas por el motor de reglas de negocio            |
| `document_processing_jobs` | Estado y metadatos de trabajos de procesamiento de PDFs        |

> Detalle completo: [data-model.md](data-model.md)

### 3.6 Capa de Almacenamiento (MinIO)

| Bucket         | Contenido                               |
| -------------- | --------------------------------------- |
| `evaluaciones` | PDFs originales tal como fueron subidos |

---

## 4. Flujo Completo: del PDF a la Consulta IA

### 4.1 Fase de Carga

```
Usuario                Frontend              Backend API            MinIO           PostgreSQL
  │                       │                      │                    │                  │
  │── selecciona PDF ────▶│                      │                    │                  │
  │                       │── POST /documentos ─▶│                    │                  │
  │                       │   (multipart/form)   │── put_object() ──▶│                  │
  │                       │                      │                    │── almacena PDF   │
  │                       │                      │── INSERT ─────────────────────────────▶│
  │                       │                      │   (estado: "pendiente")               │
  │                       │                      │── enqueue(BackgroundTask)
  │                       │◀── 202 Accepted ─────│                                       │
  │◀── "PDF en cola" ─────│                                                              │
```

**Puntos clave:**

- El backend responde `202 Accepted` inmediatamente. No espera el procesamiento
- El PDF se almacena en MinIO antes de encolar. Si el procesamiento falla, el archivo no se pierde
- Se calcula hash SHA-256 del PDF para detectar duplicados

### 4.2 Fase de Procesamiento (BackgroundTask)

```
BackgroundTask         MinIO          pdf_parser        classifier         PostgreSQL
     │                   │                │                  │                  │
     │── get_object() ──▶│                │                  │                  │
     │◀── PDF bytes ─────│                │                  │                  │
     │── extraer texto ──────────────────▶│                  │                  │
     │◀── ParsedEvaluacion ───────────────│                  │                  │
     │── clasificar comentarios ────────────────────────────▶│                  │
     │◀── ClassificationResult[] ──────────────────────────│                  │
     │── INSERT evaluacion + dimensiones + cursos + comentarios ──────────────▶│
     │── UPDATE documento (estado: "completado") ─────────────────────────────▶│
```

**Pipeline BackgroundTask:**

```
process_pdf → parse_evaluacion → classify_comments → persist (transacción)
```

Todo ocurre en una sola tarea con transacción atómica. Si falla cualquier paso, se hace rollback y `documentos.estado = "error"`.

### 4.3 Fase de Consulta IA (RAG)

```
Usuario               Frontend              QueryService           PostgreSQL        Gemini API
  │                      │                      │                     │                  │
  │── pregunta ─────────▶│                      │                     │                  │
  │                      │── POST /query ──────▶│                     │                  │
  │                      │                      │── _retrieve_metrics ▶│                  │
  │                      │                      │── _retrieve_comments▶│                  │
  │                      │                      │◀── evidencia ────────│                  │
  │                      │                      │── answer_query ──────────────────────▶│
  │                      │                      │◀── respuesta + tokens ───────────────│
  │                      │                      │── log_call (auditoría) ──────────────▶│
  │                      │◀── QueryResponse ────│                                        │
  │◀── respuesta + citas─│                                                               │
```

**Tipos de consulta soportados:**

| Tipo                | Mecanismo                | Ejemplo                                  |
| ------------------- | ------------------------ | ---------------------------------------- |
| Filtro estructurado | SQL WHERE                | Evaluaciones del docente X en periodo Y  |
| Consulta IA (RAG)   | SQL retrieval + Gemini   | "¿Cómo es la metodología de Juan Pérez?" |
| Agregación          | SQL GROUP BY + funciones | Promedio de puntuaciones por dimensión   |

---

## 5. Módulos Principales

### 5.1 Backend (Arquitectura Hexagonal)

```
backend/app/
├── api/                           → Capa de transporte HTTP
│   ├── rate_limit.py              → Rate limiter (Redis + fallback in-memory)
│   ├── deps.py                    → Dependency injection (DB, storage, Gemini)
│   └── v1/
│       ├── router.py              → Agregador de routers con prefijo /api/v1
│       ├── documentos.py          → Upload, listado, periodos, eliminación
│       ├── evaluaciones.py        → Listado con filtros (modalidad, periodo, docente)
│       ├── analytics.py           → 5 endpoints BI (resumen, docentes, dimensiones, evolución, ranking)
│       ├── qualitative.py         → 7 endpoints análisis cualitativo
│       ├── query.py               → Consultas IA (RAG + Gemini) con rate limiting
│       ├── dashboard.py           → Dashboard ejecutivo (KPIs, tendencias, insights)
│       └── alertas.py             → CRUD alertas con filtros y rebuild
├── application/                   → Lógica de aplicación (casos de uso)
│   ├── parsing/                   → Parser determinístico de PDFs
│   │   ├── parser.py              → Función principal parse_evaluacion()
│   │   ├── constants.py           → Regex anchors, noise values, PeriodoData
│   │   ├── schemas.py             → ParsedEvaluacion, HeaderData, etc.
│   │   ├── errors.py              → ParseResult, ParseError, ParseWarning
│   │   └── extractors/            → 4 extractores especializados
│   │       ├── header.py          → Profesor, periodo, recinto
│   │       ├── metrics.py         → Dimensiones pedagógicas
│   │       ├── courses.py         → Cursos y grupos
│   │       └── comments.py        → Comentarios cualitativos
│   ├── classification/            → Clasificador de comentarios
│   │   └── __init__.py            → classify_comment(), temas, sentimiento
│   └── services/                  → 9 servicios de aplicación
│       ├── processing_service.py  → Pipeline: parseo → clasificación → persistencia
│       ├── document_service.py    → CRUD documentos + MinIO
│       ├── analytics_service.py   → Métricas con caché (modalidad-aware)
│       ├── qualitative_service.py → Análisis cualitativo con caché
│       ├── query_service.py       → Orquestador RAG: retrieval → Gemini → audit
│       ├── alert_engine.py        → Motor de reglas: BAJO_DESEMPEÑO, CAIDA, SENTIMIENTO, PATRON
│       ├── alerta_service.py      → Gestión de alertas (listado, estado)
│       ├── dashboard_service.py   → Agregaciones para dashboard ejecutivo
│       └── gemini_enrichment_service.py → Enriquecimiento IA de comentarios
├── domain/                        → Entidades y reglas de negocio
│   ├── entities/                  → 9 modelos SQLAlchemy
│   │   ├── base.py                → UUIDMixin, TimestampMixin
│   │   ├── documento.py           → PDF subido
│   │   ├── evaluacion.py          → Datos extraídos (con modalidad, año, periodo_orden)
│   │   ├── evaluacion_dimension.py→ Puntajes por dimensión
│   │   ├── evaluacion_curso.py    → Datos por curso-grupo
│   │   ├── comentario_analisis.py → Comentario clasificado
│   │   ├── gemini_audit_log.py    → Auditoría de llamadas a Gemini
│   │   ├── alerta.py              → Alertas generadas por reglas de negocio
│   │   ├── document_processing_job.py → Estado de trabajos de procesamiento
│   │   └── enums.py               → Enumeraciones (Modalidad, TipoAlerta, Severidad, etc.)
│   ├── schemas/                   → DTOs Pydantic (request/response)
│   └── exceptions.py             → Excepciones de dominio (Gemini*, NotFound, Duplicate)
├── infrastructure/                → Adaptadores de infraestructura
│   ├── database/
│   │   ├── session.py             → AsyncSession factory, get_db
│   │   └── migrations/            → Alembic (9 migraciones: 0001-0009)
│   ├── external/
│   │   ├── gemini_gateway.py      → Wrapper async google-genai SDK
│   │   └── prompt_templates.py    → System prompt + templates
│   ├── repositories/              → 6 repositorios SQL
│   │   ├── evaluacion.py          → CRUD + list_filtered, count_filtered
│   │   ├── documento.py           → CRUD + periodos, por hash
│   │   ├── analytics_repo.py      → Queries analíticas (modalidad-aware)
│   │   ├── qualitative_repo.py    → Queries cualitativas (modalidad-aware)
│   │   ├── alerta_repo.py         → CRUD alertas con filtros + paginación
│   │   └── gemini_audit.py        → Log de auditoría Gemini
│   ├── storage/
│   │   ├── file_storage.py        → Protocolo de almacenamiento
│   │   └── minio_client.py        → Cliente MinIO (upload/download/delete)
│   └── tasks/
│       └── celery_app.py          → Configuración Celery + Redis (reservado para migración futura)
└── core/
    ├── config.py                  → Settings (BaseSettings + validación producción)
    ├── cache.py                   → Decorador @cached con TTL para Redis
    └── logging.py                 → Configuración de logger
```

### 5.2 Frontend (Next.js App Router)

```
frontend/src/
├── app/                             → Pages (App Router MPA)
│   ├── (dashboard)/
│   │   ├── inicio/page.tsx          → Homepage con dashboard ejecutivo
│   │   ├── carga/page.tsx           → Subida de PDFs con drag & drop
│   │   ├── biblioteca/page.tsx      → Biblioteca de documentos
│   │   ├── estadisticas/page.tsx    → Dashboard analítico (métricas, gráficas)
│   │   ├── sentimiento/page.tsx     → Análisis cualitativo (comentarios, sentimiento)
│   │   ├── docentes/page.tsx        → Ranking y detalles de docentes
│   │   ├── reportes/page.tsx        → Alertas y reportes
│   │   ├── consultas-ia/page.tsx    → Consultas inteligentes (RAG + Gemini)
│   │   └── layout.tsx               → Sidebar + navbar del dashboard
│   ├── layout.tsx                   → Layout raíz (html, head, fonts)
│   └── page.tsx                     → Redirect a inicio
├── components/
│   ├── ui/                          → shadcn/ui (Button, Card, Dialog, etc.)
│   ├── dashboard/                   → KPICard, CommandCenter, RankingTable, Charts
│   ├── consultas-ia/                → QueryInput, QueryResponse, QueryEvidence
│   ├── upload/                      → UploadPanel, DropZone, FileItem
│   ├── sentimiento/                 → QualitativeDashboard, states, distribuciones
│   └── layout/                      → Sidebar, AppSidebar, ThemeToggle
├── hooks/                           → useQuery, useUpload, useDebounce
├── lib/
│   ├── api/                         → Clientes tipados: analytics, qualitative, documents,
│   │                                  dashboard, alertas, query
│   ├── api-client.ts                → Fetch wrapper con manejo de errores
│   ├── business-rules.ts            → 150+ reglas de negocio (BR-*)
│   ├── periodo-sort.ts              → Ordenamiento de períodos
│   └── utils.ts                     → cn(), formatters
├── styles/                          → Tailwind CSS v4 globals
└── types/                           → TypeScript interfaces para API schemas
```

### 5.3 Infraestructura

```
infra/
├── docker/
│   ├── docker-compose.yml           → Stack completa de producción
│   ├── docker-compose.dev.yml       → Overrides para desarrollo (volumes, hot reload)
│   ├── nginx/nginx.conf             → Proxy reverso, TLS, rate limiting
│   └── postgres/init.sql            → CREATE EXTENSION vector
└── scripts/
    ├── setup-dev.sh                 → Bootstrap del entorno de desarrollo
    └── seed-db.sh                   → Datos iniciales para testing
```

---

## 6. Decisiones Técnicas Clave

### 6.1 Decisiones de Stack

| #   | Decisión                     | Alternativa descartada        | Justificación                                                                                 |
| --- | ---------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------- |
| D1  | **Monorepo**                 | Repos separados               | Un equipo, un producto. Co-versionado simplifica PRs y deploys. Un solo CI pipeline           |
| D2  | **FastAPI async**            | Django, Flask                 | Async nativo, tipado con Pydantic 100% integrado, OpenAPI automática, rendimiento superior    |
| D3  | **Next.js App Router (MPA)** | Pages Router, Vite+React      | Route groups para layouts por sección, Server Components, streaming, formato MPA natural      |
| D4  | **pgvector**                 | Pinecone, Weaviate, ChromaDB  | On-prem sin dependencia externa, misma instancia PostgreSQL, consultas SQL+vector en un query |
| D5  | **MinIO**                    | Sistema de archivos, S3       | API 100% compatible S3, UI de admin, replicable, migración futura a S3 trivial                |
| D6  | **FastAPI BackgroundTasks**  | Celery, Dramatiq, RQ, ARQ     | Suficiente para volumen actual. Sin infraestructura adicional. Migrable a Celery si escala    |
| D7  | **PyMuPDF (fitz)**           | pdfplumber, Tabula, pypdf     | Más rápido en benchmarks, soporte completo de texto + layout, mantenido activamente           |
| D8  | **Gemini API**               | OpenAI, Claude API, local LLM | Disponibilidad, costo competitivo, buen rendimiento en extracción estructurada                |

### 6.2 Decisiones de Diseño

| #   | Decisión                                  | Justificación                                                                                                                  |
| --- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| D9  | **Procesamiento async (no síncrono)**     | Un PDF puede tardar 5-30s en procesarse. Bloquear el request HTTP degradaría la UX. El usuario recibe feedback inmediato       |
| D10 | **Versionado de API (/api/v1/)**          | Cuando el formato de PDF cambie, v2 puede coexistir sin romper clientes existentes                                             |
| D11 | **Services desacoplados de FastAPI**      | Los services se invocan desde endpoints y desde BackgroundTasks. No dependen del ciclo HTTP                                    |
| D12 | **Hash SHA-256 para deduplicación**       | Previene procesamiento duplicado de un mismo PDF                                                                               |
| D13 | **Texto a Gemini, nunca el PDF**          | Minimiza datos sensibles enviados externamente. El PDF nunca sale de la red interna                                            |
| D14 | **Pipeline secuencial en BackgroundTask** | Un solo paso atómico: parseo → clasificación → enriquecimiento → persistencia. Migrable a Celery si se necesita retry granular |

### 6.3 Decisiones de Infraestructura

| #   | Decisión                           | Justificación                                                                          |
| --- | ---------------------------------- | -------------------------------------------------------------------------------------- |
| D15 | **Docker Compose (no Kubernetes)** | Complejidad apropiada para despliegue on-prem con volumen bajo-medio. Operación simple |
| D16 | **Nginx como proxy reverso**       | TLS termination, rate limiting, static files, health checks en un solo punto           |
| D17 | **Proxmox como hipervisor**        | Infraestructura existente. VMs aisladas para cada entorno (dev, staging, prod)         |

---

## 7. Riesgos y Mitigaciones

### 7.1 Riesgos Técnicos

| #   | Riesgo                                      | Probabilidad | Impacto | Mitigación                                                                                                                              |
| --- | ------------------------------------------- | ------------ | ------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| R1  | **Gemini API no disponible o rate limited** | Media        | Alto    | Retry con backoff exponencial en GeminiGateway. Procesamiento de PDFs no depende de Gemini (solo consultas IA)                          |
| R2  | **PDFs con formato inesperado**             | Media        | Medio   | Validación de estructura en `pdf_parser` antes de enviar a Gemini. Log detallado de PDFs rechazados. Endpoint de reprocesamiento manual |
| R3  | **Crecimiento de datos en pgvector**        | Baja         | Medio   | Índice HNSW con parámetros tuneables. Particionamiento por periodo si supera 1M registros. Monitoreo de query time                      |
| R4  | **Fuga de datos sensibles a Gemini**        | Baja         | Alto    | Solo se envía texto extraído, nunca el PDF. Se puede agregar capa de anonimización antes del envío. Logs de auditoría de cada llamada   |
| R5  | **Caída de MinIO**                          | Baja         | Alto    | MinIO soporta replicación. Backups periódicos del bucket a volumen externo. Health check en Docker Compose con restart policy           |
| R6  | **Inconsistencia entre MinIO y PostgreSQL** | Baja         | Medio   | Registro en BD se crea después de confirmar upload a MinIO. Tarea de reconciliación periódica para detectar huérfanos                   |

### 7.2 Riesgos Operacionales

| #   | Riesgo                                           | Probabilidad | Impacto | Mitigación                                                                                                                                        |
| --- | ------------------------------------------------ | ------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| R7  | **Pérdida de datos por fallo de VM**             | Baja         | Crítico | Backups diarios de PostgreSQL (pg_dump). MinIO con replicación o backup. Docker volumes en storage redundante de Proxmox                          |
| R8  | **Actualización de Gemini API rompe respuestas** | Media        | Medio   | Versionar el modelo usado (e.g., `gemini-2.5-flash`). Schema Pydantic estricto valida respuesta. Tests de integración contra API real             |
| R9  | **Equipo no familiarizado con el stack**         | Media        | Medio   | Documentación detallada. ADRs para cada decisión. README por módulo. Makefile simplifica operaciones                                              |
| R10 | **Degradación de rendimiento con volumen**       | Baja         | Medio   | Índices en columnas de filtro frecuente. Connection pooling con SQLAlchemy. BackgroundTasks migrable a Celery si necesario. Monitoreo con pg_stat |

### 7.3 Matriz de Prioridad

```
              Alta probabilidad
                    │
         R1  R8     │    R9
                    │
   Alto ────────────┼──────────── Bajo
   impacto          │          impacto
         R4  R7     │    R3  R6
                    │
              Baja probabilidad
```

**Acción inmediata (alto impacto + alta probabilidad):** R1 (retry Gemini), R8 (versionado de modelo)
**Monitorear (alto impacto + baja probabilidad):** R4 (fuga de datos), R7 (pérdida de datos)

---

## 8. Infraestructura On-Premise

### 8.1 Topología en Proxmox

```
Proxmox Host
├── VM: evaluaciones-prod
│   ├── Docker: nginx (proxy)
│   ├── Docker: frontend (next.js)
│   ├── Docker: backend (fastapi)
│   ├── Docker: postgres + pgvector
│   ├── Docker: redis
│   ├── Docker: minio
│   └── Docker: celery-worker (perfil opcional, reservado para migración futura)
│
└── VM: evaluaciones-dev (opcional)
    └── (misma topología, datos de prueba)
```

### 8.2 Puertos Internos

| Servicio      | Puerto  | Exposición                          |
| ------------- | ------- | ----------------------------------- |
| Nginx         | 80, 443 | Única entrada pública (red interna) |
| Next.js       | 3000    | Solo vía Nginx                      |
| FastAPI       | 8000    | Solo vía Nginx                      |
| PostgreSQL    | 5432    | Solo red Docker                     |
| Redis         | 6379    | Solo red Docker                     |
| MinIO API     | 9000    | Solo red Docker                     |
| MinIO Console | 9001    | Solo vía Nginx (admin)              |
| Flower        | 5555    | Solo vía Nginx (admin)              |

### 8.3 Requisitos Estimados de Recursos

| Recurso                  | Desarrollo | Producción                                       |
| ------------------------ | ---------- | ------------------------------------------------ |
| CPU                      | 4 vCPU     | 8 vCPU                                           |
| RAM                      | 8 GB       | 16 GB                                            |
| Disco (OS + Docker)      | 40 GB SSD  | 80 GB SSD                                        |
| Disco (datos: PDFs + DB) | 20 GB      | Depende del volumen (estimar 1 GB / 10,000 PDFs) |

---

## Apéndice: Diagrama de Dependencias entre Servicios

```
                    ┌──────────┐
                    │  Nginx   │
                    └────┬─────┘
                    ┌────┴─────┐
              ┌─────┤          ├─────┐
              ▼     │          │     ▼
        ┌──────────┐│    ┌──────────┐
        │ Frontend ││    │ Backend  │
        └──────────┘│    └──┬──┬──┬─┘
                    │       │  │  │
                    │       │  │  └────────▶ MinIO
                    │       │  └───────────▶ Redis (cache / rate-limit)
                    │       └──────────────▶ PostgreSQL
                    │                          ▲
                    │                          │
                    │                    (BackgroundTask escribe resultados)
                    └──────────────────────────────────────────────────
```
