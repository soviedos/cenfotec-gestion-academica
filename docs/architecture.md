# Arquitectura del Sistema

> Documento técnico de arquitectura para la plataforma **Evaluaciones Docentes**.
> Última actualización: 2026-04-02

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
│              ┌─────────────┐          ┌───────────┐  ┌────────────┐   │
│              │ PostgreSQL  │          │   Redis    │  │   MinIO    │   │
│              │ + pgvector  │          │   :6379    │  │ :9000/:9001│   │
│              │    :5432    │          └─────┬──────┘  └────────────┘   │
│              └─────────────┘                │                         │
│                                      ┌──────▼──────┐                  │
│                                      │   Celery    │                  │
│                                      │   Worker(s) │                  │
│                                      └──────┬──────┘                  │
│                                             │                         │
└─────────────────────────────────────────────┼─────────────────────────┘
                                              │ HTTPS (solo texto)
                                       ┌──────▼──────┐
                                       │  Gemini API │
                                       │  (externo)  │
                                       └─────────────┘
```

### Capas del sistema

| Capa               | Componente            | Responsabilidad principal                            |
| ------------------ | --------------------- | ---------------------------------------------------- |
| **Presentación**   | Next.js (App Router)  | Renderizado de páginas, interacción con el usuario   |
| **Proxy**          | Nginx                 | Terminación TLS, enrutamiento, rate limiting         |
| **API**            | FastAPI               | Validación, autenticación, orquestación de servicios |
| **Dominio**        | Services (Python)     | Lógica de negocio pura: parseo, análisis, reportes   |
| **Procesamiento**  | Celery Workers        | Ejecución asíncrona de tareas pesadas                |
| **Persistencia**   | PostgreSQL + pgvector | Datos estructurados + embeddings vectoriales         |
| **Almacenamiento** | MinIO                 | Archivos binarios (PDFs originales)                  |
| **Mensajería**     | Redis                 | Broker de tareas Celery + caché ligero               |
| **IA externa**     | Gemini API            | Análisis semántico y generación de embeddings        |

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
| Orquestación               | Recibe requests, delega al service o encola tarea Celery  |
| Serialización de respuesta | Schemas de salida garantizan formato consistente          |
| Documentación automática   | OpenAPI/Swagger generado automáticamente                  |

**No hace:** transformación de datos compleja, acceso directo a Gemini, almacenamiento de archivos.

### 3.3 Capa de Dominio (Services)

| Responsabilidad     | Detalle                                                      |
| ------------------- | ------------------------------------------------------------ |
| `pdf_parser`        | Extrae texto estructurado del PDF usando PyMuPDF             |
| `gemini_analyzer`   | Envía texto a Gemini, recibe análisis estructurado en JSON   |
| `embedding_service` | Genera embeddings vectoriales y los almacena en pgvector     |
| `reporte_generator` | Agrega datos por docente, periodo, facultad; genera métricas |

**Principio:** los servicios son funciones puras o clases sin dependencia de FastAPI. Se invocan desde endpoints y desde tareas Celery indistintamente.

### 3.4 Capa de Procesamiento (Celery)

| Responsabilidad         | Detalle                                                         |
| ----------------------- | --------------------------------------------------------------- |
| Procesamiento asíncrono | Desacopla la carga del PDF de su análisis                       |
| Pipeline encadenado     | `upload → parseo → análisis → embeddings` como cadena de tareas |
| Retry automático        | Reintentos con backoff exponencial ante fallos de Gemini API    |
| Monitoreo               | Flower (UI) para inspección de tareas en tiempo real            |

### 3.5 Capa de Persistencia (PostgreSQL + pgvector)

| Tabla                   | Propósito                                                             |
| ----------------------- | --------------------------------------------------------------------- |
| `documentos`            | Metadatos del PDF (nombre, hash, ruta MinIO, estado de procesamiento) |
| `evaluaciones`          | Datos estructurados extraídos de cada evaluación                      |
| `docentes`              | Catálogo de docentes evaluados                                        |
| `periodos`              | Periodos académicos                                                   |
| `usuarios`              | Usuarios del sistema con roles                                        |
| `embeddings` (pgvector) | Vectores de las evaluaciones para búsqueda semántica                  |

### 3.6 Capa de Almacenamiento (MinIO)

| Bucket                  | Contenido                               |
| ----------------------- | --------------------------------------- |
| `documentos-raw`        | PDFs originales tal como fueron subidos |
| `documentos-procesados` | Texto extraído en formato JSON (backup) |

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
  │                       │                      │── enqueue task ──▶ Redis              │
  │                       │◀── 202 Accepted ─────│                                       │
  │◀── "PDF en cola" ─────│                                                              │
```

**Puntos clave:**

- El backend responde `202 Accepted` inmediatamente. No espera el procesamiento
- El PDF se almacena en MinIO antes de encolar. Si Celery falla, el archivo no se pierde
- Se calcula hash SHA-256 del PDF para detectar duplicados

### 4.2 Fase de Procesamiento (Celery Worker)

```
Celery Worker          MinIO          pdf_parser        gemini_analyzer       PostgreSQL
     │                   │                │                    │                   │
     │── get_object() ──▶│                │                    │                   │
     │◀── PDF bytes ─────│                │                    │                   │
     │── extraer texto ──────────────────▶│                    │                   │
     │◀── texto estructurado ─────────────│                    │                   │
     │── analizar con IA ─────────────────────────────────────▶│                   │
     │◀── JSON estructurado ──────────────────────────────────│                   │
     │── generar embedding ──────────────────────────────────▶│                   │
     │◀── vector [1536 dims] ────────────────────────────────│                   │
     │── INSERT evaluacion + embedding ────────────────────────────────────────▶│
     │── UPDATE documento (estado: "completado") ──────────────────────────────▶│
```

**Pipeline Celery (cadena de tareas):**

```
task_parse_pdf  →  task_analyze_with_gemini  →  task_generate_embeddings  →  task_update_status
```

Cada tarea es independiente y retryable. Si `task_analyze_with_gemini` falla por rate limit de Gemini, reintenta con backoff exponencial sin reprocesar el parseo.

### 4.3 Fase de Consulta

```
Usuario               Frontend              Backend API           PostgreSQL
  │                      │                      │                     │
  │── busca "didáctica" ▶│                      │                     │
  │                      │── GET /evaluaciones  │                     │
  │                      │   ?q=didáctica ──────▶│                     │
  │                      │                      │── query SQL ───────▶│
  │                      │                      │   + búsqueda vector │
  │                      │                      │◀── resultados ──────│
  │                      │◀── JSON ─────────────│                     │
  │◀── tabla resultados ─│                                            │
```

**Tipos de consulta soportados:**

| Tipo                | Mecanismo                   | Ejemplo                                         |
| ------------------- | --------------------------- | ----------------------------------------------- |
| Filtro estructurado | SQL WHERE                   | Evaluaciones del docente X en periodo Y         |
| Búsqueda por texto  | `tsvector` Full-Text Search | Evaluaciones que mencionan "metodología"        |
| Búsqueda semántica  | pgvector cosine similarity  | Evaluaciones similares a "buen manejo del aula" |
| Agregación          | SQL GROUP BY + funciones    | Promedio de puntuaciones por facultad           |

---

## 5. Módulos Principales

### 5.1 Backend

```
backend/app/
├── api/v1/
│   ├── documentos.py          → Upload, listado y estado de PDFs
│   ├── evaluaciones.py        → CRUD y búsqueda de evaluaciones
│   ├── reportes.py            → Agregaciones y métricas
│   ├── auth.py                → Login, logout, sesión
│   └── router.py              → Agregador de routers con prefijo /api/v1
├── services/
│   ├── pdf_parser.py          → Extracción de texto con PyMuPDF
│   ├── gemini_analyzer.py     → Prompt engineering + llamada a Gemini
│   ├── embedding_service.py   → Generación de vectores y búsqueda
│   └── reporte_generator.py   → Lógica de reportes y estadísticas
├── tasks/
│   ├── celery_app.py          → Configuración broker, serializer, retries
│   ├── pdf_processing.py      → Tarea: pipeline completo de PDF
│   └── analysis.py            → Tarea: re-análisis bajo demanda
├── models/                    → SQLAlchemy: Documento, Evaluacion, Docente, Usuario
├── schemas/                   → Pydantic: validación request/response
├── db/                        → Session, engine, Alembic migrations
└── storage/                   → Cliente MinIO abstracción put/get/delete
```

### 5.2 Frontend

```
frontend/src/
├── app/                             → Pages (App Router MPA)
│   ├── (dashboard)/
│   │   ├── carga/page.tsx           → Subida de PDFs con drag & drop
│   │   ├── evaluaciones/page.tsx    → Listado con filtros y búsqueda
│   │   ├── evaluaciones/[id]/page.tsx → Detalle de evaluación
│   │   ├── reportes/page.tsx        → Dashboard de métricas
│   │   └── layout.tsx               → Sidebar + navbar del dashboard
│   ├── (auth)/
│   │   └── login/page.tsx           → Pantalla de autenticación
│   ├── layout.tsx                   → Layout raíz (html, head, fonts)
│   └── page.tsx                     → Redirect a /carga o /login
├── components/
│   ├── ui/                          → Button, Input, Card, Modal, Table
│   ├── evaluaciones/                → EvaluacionCard, EvaluacionFilters
│   ├── reportes/                    → ChartBar, MetricCard, ExportButton
│   └── layout/                      → Navbar, Sidebar, Footer
├── hooks/                           → useEvaluaciones, useUpload, useDebounce
├── lib/
│   ├── api-client.ts                → Fetch wrapper con base URL y auth
│   ├── auth.ts                      → Token management
│   └── utils.ts                     → Formatters, validators
└── types/                           → Evaluacion, Documento, Docente, ApiResponse
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
| D6  | **Celery + Redis**           | Dramatiq, RQ, ARQ             | Ecosistema maduro, retry policies configurables, monitoreo con Flower, amplia documentación   |
| D7  | **PyMuPDF (fitz)**           | pdfplumber, Tabula, pypdf     | Más rápido en benchmarks, soporte completo de texto + layout, mantenido activamente           |
| D8  | **Gemini API**               | OpenAI, Claude API, local LLM | Disponibilidad, costo competitivo, buen rendimiento en extracción estructurada                |

### 6.2 Decisiones de Diseño

| #   | Decisión                              | Justificación                                                                                                            |
| --- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| D9  | **Procesamiento async (no síncrono)** | Un PDF puede tardar 5-30s en procesarse. Bloquear el request HTTP degradaría la UX. El usuario recibe feedback inmediato |
| D10 | **Versionado de API (/api/v1/)**      | Cuando el formato de PDF cambie, v2 puede coexistir sin romper clientes existentes                                       |
| D11 | **Services desacoplados de FastAPI**  | Los services se invocan desde endpoints y desde tareas Celery. No dependen del ciclo HTTP                                |
| D12 | **Hash SHA-256 para deduplicación**   | Previene procesamiento duplicado de un mismo PDF                                                                         |
| D13 | **Texto a Gemini, nunca el PDF**      | Minimiza datos sensibles enviados externamente. El PDF nunca sale de la red interna                                      |
| D14 | **Pipeline Celery en cadena**         | Cada paso es retryable de forma independiente. Un fallo en embeddings no obliga a reparsear el PDF                       |

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
| R1  | **Gemini API no disponible o rate limited** | Media        | Alto    | Retry con backoff exponencial. Cola Celery retiene tareas. Procesamiento no se pierde, solo se retrasa                                  |
| R2  | **PDFs con formato inesperado**             | Media        | Medio   | Validación de estructura en `pdf_parser` antes de enviar a Gemini. Log detallado de PDFs rechazados. Endpoint de reprocesamiento manual |
| R3  | **Crecimiento de datos en pgvector**        | Baja         | Medio   | Índice HNSW con parámetros tuneables. Particionamiento por periodo si supera 1M registros. Monitoreo de query time                      |
| R4  | **Fuga de datos sensibles a Gemini**        | Baja         | Alto    | Solo se envía texto extraído, nunca el PDF. Se puede agregar capa de anonimización antes del envío. Logs de auditoría de cada llamada   |
| R5  | **Caída de MinIO**                          | Baja         | Alto    | MinIO soporta replicación. Backups periódicos del bucket a volumen externo. Health check en Docker Compose con restart policy           |
| R6  | **Inconsistencia entre MinIO y PostgreSQL** | Baja         | Medio   | Registro en BD se crea después de confirmar upload a MinIO. Tarea de reconciliación periódica para detectar huérfanos                   |

### 7.2 Riesgos Operacionales

| #   | Riesgo                                           | Probabilidad | Impacto | Mitigación                                                                                                                                  |
| --- | ------------------------------------------------ | ------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| R7  | **Pérdida de datos por fallo de VM**             | Baja         | Crítico | Backups diarios de PostgreSQL (pg_dump). MinIO con replicación o backup. Docker volumes en storage redundante de Proxmox                    |
| R8  | **Actualización de Gemini API rompe respuestas** | Media        | Medio   | Versionar el modelo usado (e.g., `gemini-2.0-flash`). Schema Pydantic estricto valida respuesta. Tests de integración contra API real       |
| R9  | **Equipo no familiarizado con el stack**         | Media        | Medio   | Documentación detallada. ADRs para cada decisión. README por módulo. Makefile simplifica operaciones                                        |
| R10 | **Degradación de rendimiento con volumen**       | Baja         | Medio   | Índices en columnas de filtro frecuente. Connection pooling con SQLAlchemy. Celery concurrency configurable. Monitoreo con Flower + pg_stat |

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
│   ├── Docker: celery-worker (x2)
│   ├── Docker: postgres + pgvector
│   ├── Docker: redis
│   ├── Docker: minio
│   └── Docker: flower (monitoreo)
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
                    │       │  └───────────▶ Redis ──▶ Celery Worker
                    │       └──────────────▶ PostgreSQL     │
                    │                          ▲            │
                    │                          └────────────┘
                    │                       (worker escribe resultados)
                    └──────────────────────────────────────────────────
```
