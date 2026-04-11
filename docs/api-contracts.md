# Contratos de API

> Especificación completa de endpoints REST, request/response schemas y convenciones.
> Última actualización: 2026-04-11

Base URL: `http://localhost:8000/api/v1`

Documentación interactiva (Swagger): `http://localhost:8000/docs`

---

## Índice

1. [Health Check](#health-check)
2. [Documentos](#documentos) (5 endpoints)
3. [Evaluaciones](#evaluaciones) (1 endpoint)
4. [Analytics](#analytics) (8 endpoints) — `modalidad` **obligatorio** [BR-MOD-02]
5. [Qualitative](#qualitative) (7 endpoints) — `modalidad` **obligatorio** [BR-MOD-02]
6. [Query](#query) (1 endpoint) — Consultas IA (RAG + Gemini)
7. [Dashboard](#dashboard) (1 endpoint)
8. [Alertas](#alertas) (4 endpoints)
9. [Config](#config) (1 endpoint)
10. [Convenciones](#convenciones)

---

## Health Check

```
GET /health
```

**Response 200:**

```json
{
  "status": "ok | degraded",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected | unreachable"
}
```

`status` devuelve `"degraded"` si la base de datos no responde.

---

## Documentos

### Upload PDF

```
POST /api/v1/documentos/upload
Content-Type: multipart/form-data
```

| Campo  | Tipo         | Requerido | Descripción |
| ------ | ------------ | --------- | ----------- |
| `file` | `UploadFile` | Sí        | Archivo PDF |

**Response 201:**

```json
{
  "id": "uuid",
  "nombre_archivo": "evaluacion.pdf",
  "hash_sha256": "abc123...",
  "estado": "subido",
  "tamano_bytes": 204800,
  "created_at": "2026-06-04T10:00:00Z",
  "updated_at": "2026-06-04T10:00:00Z"
}
```

**Errores:** `409` si el PDF ya existe (hash duplicado).

### Listar documentos

```
GET /api/v1/documentos/
```

| Query Param      | Tipo   | Default        | Descripción                   |
| ---------------- | ------ | -------------- | ----------------------------- |
| `page`           | int    | `1`            | Página                        |
| `page_size`      | int    | `20`           | Elementos por página          |
| `sort_by`        | string | `"created_at"` | Campo de ordenamiento         |
| `sort_order`     | string | `"desc"`       | `asc` o `desc`                |
| `estado`         | string | —              | Filtrar por estado            |
| `docente`        | string | —              | Filtrar por docente           |
| `periodo`        | string | —              | Filtrar por período           |
| `nombre_archivo` | string | —              | Filtrar por nombre de archivo |

**Response 200:** `DocumentoList` (paginado con `items`, `total`, `page`, `page_size`, `total_pages`).

### Listar períodos

```
GET /api/v1/documentos/periodos
```

**Response 200:** `string[]` — Lista de períodos únicos.

### Eliminar documento

```
DELETE /api/v1/documentos/{documento_id}
```

**Response 204:** Sin contenido. Elimina documento, archivo en MinIO y evaluaciones asociadas (CASCADE).

### Descargar PDF

```
GET /api/v1/documentos/{documento_id}/download
```

**Response 200:** Archivo PDF binario (`application/pdf`), con header `Content-Disposition: inline`.

**Errores:** `404` si el documento no existe.

---

## Evaluaciones

### Listar evaluaciones

```
GET /api/v1/evaluaciones/
```

| Query Param | Tipo   | Default | Descripción                       |
| ----------- | ------ | ------- | --------------------------------- |
| `page`      | int    | `1`     | Página                            |
| `page_size` | int    | `20`    | Elementos por página              |
| `modalidad` | string | —       | Filtrar por modalidad [BR-MOD-02] |
| `periodo`   | string | —       | Filtrar por período               |
| `docente`   | string | —       | Filtrar por docente               |
| `estado`    | string | —       | Filtrar por estado                |

**Response 200:** `EvaluacionList` (paginado).

```json
{
  "items": [
    {
      "id": "uuid",
      "documento_id": "uuid",
      "docente_nombre": "Juan Pérez",
      "periodo": "I Cuatrimestre 2025",
      "materia": "Programación I",
      "puntaje_general": 85.5,
      "resumen_ia": null,
      "estado": "completado",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## Analytics

Todos los endpoints de analytics **requieren** el parámetro `modalidad` para aislamiento por modalidad [BR-MOD-02]. Adicionalmente soportan filtros opcionales `escuela` y `curso`.

### Períodos disponibles

```
GET /api/v1/analytics/periodos
```

| Query Param | Tipo   | Default | Descripción                      |
| ----------- | ------ | ------- | -------------------------------- |
| `modalidad` | string | —       | Filtrar por modalidad (opcional) |

**Response 200:** `PeriodoOption[]` — Lista de períodos con su modalidad, ordenados cronológicamente.

### Escuelas disponibles

```
GET /api/v1/analytics/escuelas
```

| Query Param | Tipo   | Default | Descripción                      |
| ----------- | ------ | ------- | -------------------------------- |
| `modalidad` | string | —       | Filtrar por modalidad (opcional) |
| `periodo`   | string | —       | Filtrar por período (opcional)   |

**Response 200:** `string[]` — Lista de escuelas.

### Cursos disponibles

```
GET /api/v1/analytics/cursos
```

| Query Param | Tipo   | Default | Descripción                      |
| ----------- | ------ | ------- | -------------------------------- |
| `escuela`   | string | —       | Filtrar por escuela (opcional)   |
| `modalidad` | string | —       | Filtrar por modalidad (opcional) |
| `periodo`   | string | —       | Filtrar por período (opcional)   |

**Response 200:** `string[]` — Lista de cursos.

### Resumen general

```
GET /api/v1/analytics/resumen
```

| Query Param | Tipo   | Default | Descripción                             |
| ----------- | ------ | ------- | --------------------------------------- |
| `modalidad` | string | **Req** | Modalidad (**obligatorio**) [BR-MOD-02] |
| `periodo`   | string | —       | Filtrar por período                     |
| `escuela`   | string | —       | Filtrar por escuela                     |
| `curso`     | string | —       | Filtrar por curso                       |

**Response 200:**

```json
{
  "promedio_global": 82.3,
  "total_evaluaciones": 150,
  "total_docentes": 45,
  "total_periodos": 6
}
```

### Promedios por docente

```
GET /api/v1/analytics/docentes
```

| Query Param | Tipo   | Default | Descripción                             |
| ----------- | ------ | ------- | --------------------------------------- |
| `modalidad` | string | **Req** | Modalidad (**obligatorio**) [BR-MOD-02] |
| `periodo`   | string | —       | Filtrar por período                     |
| `escuela`   | string | —       | Filtrar por escuela                     |
| `curso`     | string | —       | Filtrar por curso                       |
| `limit`     | int    | `50`    | Máximo resultados (1-200)               |
| `offset`    | int    | `0`     | Desplazamiento                          |

**Response 200:** `DocentePromedio[]`

### Promedios por dimensión

```
GET /api/v1/analytics/dimensiones
```

| Query Param | Tipo   | Default | Descripción                             |
| ----------- | ------ | ------- | --------------------------------------- |
| `modalidad` | string | **Req** | Modalidad (**obligatorio**) [BR-MOD-02] |
| `periodo`   | string | —       | Filtrar por período                     |
| `docente`   | string | —       | Filtrar por docente                     |
| `escuela`   | string | —       | Filtrar por escuela                     |
| `curso`     | string | —       | Filtrar por curso                       |

**Response 200:** `DimensionPromedio[]`

```json
[
  {
    "dimension": "METODOLOGÍA",
    "pct_estudiante": 85.2,
    "pct_director": 90.0,
    "pct_autoeval": 88.5,
    "pct_promedio": 87.9
  }
]
```

### Evolución por períodos

```
GET /api/v1/analytics/evolucion
```

| Query Param | Tipo   | Default | Descripción                             |
| ----------- | ------ | ------- | --------------------------------------- |
| `modalidad` | string | **Req** | Modalidad (**obligatorio**) [BR-MOD-02] |
| `docente`   | string | —       | Filtrar por docente                     |
| `escuela`   | string | —       | Filtrar por escuela                     |
| `curso`     | string | —       | Filtrar por curso                       |

**Response 200:** `PeriodoMetrica[]`

### Ranking de docentes

```
GET /api/v1/analytics/ranking
```

| Query Param | Tipo   | Default | Descripción                             |
| ----------- | ------ | ------- | --------------------------------------- |
| `modalidad` | string | **Req** | Modalidad (**obligatorio**) [BR-MOD-02] |
| `periodo`   | string | —       | Filtrar por período                     |
| `escuela`   | string | —       | Filtrar por escuela                     |
| `curso`     | string | —       | Filtrar por curso                       |
| `limit`     | int    | `10`    | Top N docentes (1-100)                  |

**Response 200:** `RankingDocente[]`

---

## Qualitative

Análisis cualitativo de comentarios. Todos los endpoints (excepto `/filtros`) **requieren** `modalidad` [BR-MOD-02].

### Filtros disponibles

```
GET /api/v1/qualitative/filtros
```

**Response 200:**

```json
{
  "periodos": ["I Cuatrimestre 2025", "..."],
  "docentes": ["Juan Pérez", "..."],
  "asignaturas": ["Programación I", "..."],
  "escuelas": ["ESC ING DEL SOFTWARE", "..."]
}
```

### Resumen cualitativo

```
GET /api/v1/qualitative/resumen
```

| Query Param  | Tipo   | Default | Descripción                             |
| ------------ | ------ | ------- | --------------------------------------- |
| `modalidad`  | string | **Req** | Modalidad (**obligatorio**) [BR-MOD-02] |
| `periodo`    | string | —       | Filtrar por período                     |
| `docente`    | string | —       | Filtrar por docente                     |
| `asignatura` | string | —       | Filtrar por asignatura                  |
| `escuela`    | string | —       | Filtrar por escuela                     |

**Response 200:** `ResumenCualitativo`

### Listar comentarios

```
GET /api/v1/qualitative/comentarios
```

Mismos filtros que resumen, más:

| Query Param   | Tipo   | Default | Descripción                               |
| ------------- | ------ | ------- | ----------------------------------------- |
| `tipo`        | string | —       | `fortaleza`, `mejora`, `observacion`      |
| `tema`        | string | —       | Filtrar por tema clasificado              |
| `sentimiento` | string | —       | `positivo`, `neutro`, `mixto`, `negativo` |
| `limit`       | int    | `50`    | Máximo resultados (1-200)                 |
| `offset`      | int    | `0`     | Desplazamiento                            |

**Response 200:** `ComentarioAnalisisRead[]`

### Distribución por temas

```
GET /api/v1/qualitative/distribucion/temas
```

Mismos filtros que resumen, más `tipo`.

**Response 200:** `TemaDistribucion[]`

### Distribución por sentimiento

```
GET /api/v1/qualitative/distribucion/sentimiento
```

Mismos filtros que resumen, más `tipo` y `tema`.

**Response 200:** `SentimientoDistribucion[]`

### Nube de palabras

```
GET /api/v1/qualitative/nube-palabras
```

Mismos filtros que resumen, más `tipo`.

**Response 200:**

```json
{
  "tipo": "fortaleza",
  "palabras": [
    { "text": "didáctica", "value": 45 },
    { "text": "puntualidad", "value": 32 }
  ]
}
```

---

## Query

Consultas en lenguaje natural con RAG (Retrieval-Augmented Generation) + Gemini API. Protegido con rate limiter (10 req/min).

### Realizar consulta

```
POST /api/v1/query
```

**Request:**

```json
{
  "question": "¿Cómo es la metodología de Juan Pérez?",
  "filters": {
    "periodo": "I Cuatrimestre 2025",
    "docente": null,
    "asignatura": null,
    "escuela": null
  }
}
```

**Response 200:**

```json
{
  "answer": "Según las evaluaciones...",
  "confidence": null,
  "evidence": [
    {
      "type": "metric",
      "label": "Promedio METODOLOGÍA",
      "value": 87.5,
      "source": { "periodo": "I Cuatrimestre 2025", "docente": "Juan Pérez" }
    },
    {
      "type": "comment",
      "texto": "Excelente manejo didáctico...",
      "source": {
        "evaluacion_id": "uuid",
        "docente": "Juan Pérez",
        "periodo": "I Cuatrimestre 2025",
        "asignatura": "Programación I",
        "fuente": "Estudiante"
      },
      "relevance_score": null
    }
  ],
  "metadata": {
    "model": "gemini-2.5-flash",
    "tokens_used": 1250,
    "latency_ms": 2300,
    "audit_log_id": "uuid"
  }
}
```

**Errores:** `429` rate limit, `503` Gemini no disponible, `504` timeout.

---

## Dashboard

### Resumen ejecutivo

```
GET /api/v1/dashboard/summary
```

| Query Param | Tipo   | Default | Descripción         |
| ----------- | ------ | ------- | ------------------- |
| `periodo`   | string | —       | Filtrar por período |

**Response 200:** `DashboardSummary` (KPIs, alertas, tendencias, top/bottom docentes, insights, actividad reciente).

---

## Alertas

Sistema de alertas automáticas basadas en reglas de negocio [AL-10 a AL-50].

### Listar alertas

```
GET /api/v1/alertas
```

| Query Param   | Tipo   | Default | Descripción                                        |
| ------------- | ------ | ------- | -------------------------------------------------- |
| `modalidad`   | string | **Req** | Modalidad (**obligatorio**) [BR-MOD-02]            |
| `anio`        | int    | —       | Filtrar por año                                    |
| `periodo`     | string | —       | Filtrar por periodo                                |
| `severidad`   | string | —       | `alta`, `media`, `baja`                            |
| `estado`      | string | —       | `activa`, `revisada`, `resuelta`, `descartada`     |
| `docente`     | string | —       | Buscar por nombre de docente                       |
| `curso`       | string | —       | Buscar por nombre de curso                         |
| `tipo_alerta` | string | —       | `BAJO_DESEMPEÑO`, `CAIDA`, `SENTIMIENTO`, `PATRON` |
| `page`        | int    | `1`     | Página                                             |
| `page_size`   | int    | `20`    | Elementos por página (1-100)                       |

**Response 200:** `AlertasPaginadas`

### Resumen de alertas

```
GET /api/v1/alertas/summary
```

| Query Param | Tipo   | Default | Descripción           |
| ----------- | ------ | ------- | --------------------- |
| `modalidad` | string | —       | Filtrar por modalidad |

**Response 200:**

```json
{
  "total_activas": 12,
  "por_severidad": { "alta": 3, "media": 5, "baja": 4 },
  "por_tipo": {
    "BAJO_DESEMPEÑO": 6,
    "CAIDA": 3,
    "SENTIMIENTO": 2,
    "PATRON": 1
  },
  "por_modalidad": { "CUATRIMESTRAL": 8, "MENSUAL": 4 },
  "docentes_afectados": 8
}
```

### Reconstruir alertas

```
POST /api/v1/alertas/rebuild
```

Ejecuta el motor de alertas sobre todas las evaluaciones. Idempotente gracias a restricciones UNIQUE [AL-40].

**Response 200:**

```json
{
  "candidates_generated": 150,
  "created_or_updated": 12,
  "modalidades_processed": 3,
  "periodos_by_modalidad": {
    "CUATRIMESTRAL": ["I Cuatrimestre 2025", "II Cuatrimestre 2025"],
    "MENSUAL": ["Enero 2025"]
  }
}
```

### Actualizar estado de alerta

```
PATCH /api/v1/alertas/{alerta_id}/estado
```

| Query Param | Tipo   | Requerido | Descripción                          |
| ----------- | ------ | --------- | ------------------------------------ |
| `estado`    | string | Sí        | `revisada`, `resuelta`, `descartada` |

**Response 200:** `AlertaResponse` actualizada.

---

## Config

### Umbrales de alerta

```
GET /api/v1/config/alert-thresholds
```

Retorna los umbrales configurados para el motor de alertas. Permite al frontend sincronizar sus constantes con la fuente de verdad del backend (`alert_rules.py`).

**Response 200:**

```json
{
  "bajo_desempeno": {
    "high": 60.0,
    "medium": 70.0,
    "low": 80.0
  },
  "caida": {
    "high": 15.0,
    "medium": 10.0,
    "low": 5.0
  },
  "sentimiento": {
    "high": 20.0,
    "medium": 10.0,
    "low": 5.0
  },
  "patron": {
    "mejora_negativo": 0.5,
    "actitud_negativo": 0.3,
    "otro": 0.4
  }
}
```

Cada categoría mapea a las constantes en `backend/app/domain/alert_rules.py` ([AL-20] a [AL-23]).

---

## Convenciones

### Paginación

Todos los endpoints que retornan listas paginadas usan el schema `PaginatedItems`:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Filtro por modalidad [BR-MOD-02]

Los endpoints de analytics y qualitative **requieren** `modalidad` como query parameter obligatorio. El valor debe ser una de las modalidades válidas: `CUATRIMESTRAL`, `MENSUAL`, `B2B`. Si se omite, el backend responde con `422`.

Los endpoints de evaluaciones y alertas aceptan `modalidad` como filtro opcional.

### Manejo de errores

| Código | Significado                              |
| ------ | ---------------------------------------- |
| `400`  | Error de dominio (validación de negocio) |
| `404`  | Recurso no encontrado                    |
| `409`  | Conflicto (documento duplicado)          |
| `422`  | Error de validación Pydantic             |
| `429`  | Rate limit excedido (endpoint `/query`)  |
| `502`  | Error de Gemini API                      |
| `503`  | Gemini no disponible o rate limited      |
| `504`  | Timeout de Gemini                        |

Formato de error estándar:

```json
{
  "detail": "Mensaje descriptivo del error",
  "code": "OPTIONAL_ERROR_CODE"
}
```

### Seguridad

- Headers de seguridad: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`
- En producción: `Strict-Transport-Security` y `Content-Security-Policy`
- Rate limiting en `/query`: 10 requests/minuto por IP (Redis con fallback in-memory)
