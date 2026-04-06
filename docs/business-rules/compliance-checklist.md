# Checklist de Cumplimiento — Reglas de Negocio

> **Fuente:** `docs/business-rules/evaluation-rules.md` v1.0.0  
> **Uso:** PR reviews, QA manual, auditorías técnicas  
> **Instrucciones:** Marcar `[x]` cuando se verifique. Anotar N/A si no aplica al cambio.

---

## 1. Parser (`[BR-PROC-*]`, `[BR-BE-01]`)

### 1.1 Pipeline

| #   | Regla          | Check | Verificación                                                                                                                                                              |
| --- | -------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| 1   | `[BR-PROC-01]` | `[ ]` | El pipeline sigue los 10 pasos en orden: recepción → dedup SHA-256 → MinIO → header → métricas → cursos → comentarios → clasificación → persistencia → enriquecimiento IA |
| 2   | `[BR-PROC-02]` | `[ ]` | El parser es función pura determinística — sin estado externo, sin I/O de red                                                                                             |
| 3   | `[BR-PROC-03]` | `[ ]` | El parser no lanza excepciones — retorna `ParseResult` con `data                                                                                                          | None`+`errors`+`warnings`+`metadata` |

### 1.2 Extracción de encabezado

| #   | Regla          | Check | Verificación                                                                                 |
| --- | -------------- | ----- | -------------------------------------------------------------------------------------------- |
| 4   | `[BR-PROC-10]` | `[ ]` | Campos fatales: `profesor_nombre`, `periodo`, `recinto`. Si falta alguno → PDF no se procesa |
| 5   | `[BR-PROC-11]` | `[ ]` | `profesor_codigo` es opcional (extraído de paréntesis tras nombre)                           |
| 6   | `[BR-BE-01]`   | `[ ]` | `HeaderData` valida: `profesor_nombre` min=2 max=300, `periodo` min=2 max=50                 |

### 1.3 Extracción de métricas

| #   | Regla          | Check | Verificación                                                                      |
| --- | -------------- | ----- | --------------------------------------------------------------------------------- |
| 7   | `[BR-PROC-20]` | `[ ]` | Dimensiones reconocidas: METODOLOGÍA, Dominio, CUMPLIMIENTO, ESTRATEGIA, GENERAL  |
| 8   | `[BR-PROC-21]` | `[ ]` | Cada dimensión tiene exactamente 3 fuentes: Estudiante, Director, Autoevaluación  |
| 9   | `[BR-PROC-22]` | `[ ]` | Puntajes parseados con regex `([\d.]+)\s*/\s*([\d.]+)`                            |
| 10  | `[BR-PROC-23]` | `[ ]` | Porcentajes en `[0, 100]` — fuera de rango → `ParseWarning`                       |
| 11  | `[BR-PROC-24]` | `[ ]` | Si falta fila de resumen → se calcula como promedio de dimensiones                |
| 12  | `[BR-BE-01]`   | `[ ]` | `FuentePuntaje`: `puntos_obtenidos ≥ 0`, `puntos_maximos > 0`, `porcentaje 0–100` |
| 13  | `[BR-BE-01]`   | `[ ]` | `ParsedEvaluacion`: `dimensiones min_length=1`, `cursos min_length=1`             |

### 1.4 Extracción de cursos

| #   | Regla          | Check | Verificación                                                            |
| --- | -------------- | ----- | ----------------------------------------------------------------------- |
| 14  | `[BR-CONS-30]` | `[ ]` | `respondieron ≤ matriculados` — si se viola → `ParseWarning` (no fatal) |
| 15  | `[BR-CONS-31]` | `[ ]` | Código de curso contiene guión (`INF-02`). Filas sin guión se descartan |

### 1.5 Clasificación de comentarios

| #   | Regla          | Check | Verificación                                                                             |
| --- | -------------- | ----- | ---------------------------------------------------------------------------------------- |
| 16  | `[BR-CLAS-01]` | `[ ]` | Tipo por columna: col 0 → `fortaleza`, col 1 → `mejora`, col 2 → `observacion`           |
| 17  | `[BR-CLAS-02]` | `[ ]` | Ruido descartado: `"."`, `"-"`, `"n/a"`, `"sin comentarios"`, etc.                       |
| 18  | `[BR-CLAS-03]` | `[ ]` | Texto máximo: 10,000 chars. Más largo → truncar                                          |
| 19  | `[BR-CLAS-10]` | `[ ]` | Tema asignado por keywords — 10 temas válidos, first-match wins, fallback `otro`         |
| 20  | `[BR-CLAS-11]` | `[ ]` | `tema_confianza = "regla"` para clasificación por keywords                               |
| 21  | `[BR-CLAS-20]` | `[ ]` | Sentimiento por puntaje de keywords con prior por tipo (fortaleza +1 pos, mejora +1 neg) |
| 22  | `[BR-CLAS-21]` | `[ ]` | `sent_score` almacenado como float `[-1.0, 1.0]`                                         |

### 1.6 Determinación de modalidad y periodo

| #   | Regla         | Check | Verificación                                                                                  |
| --- | ------------- | ----- | --------------------------------------------------------------------------------------------- |
| 23  | `[BR-MOD-01]` | `[ ]` | Cada evaluación pertenece a exactamente una modalidad                                         |
| 24  | `[BR-MOD-03]` | `[ ]` | `determinar_modalidad()` infiere desde periodo: `B2B > CUATRIMESTRAL > MENSUAL > DESCONOCIDA` |
| 25  | `[BR-BE-20]`  | `[ ]` | Periodo normalizado: `normalizar_periodo()` → UPPER, espacios únicos, sin guiones             |
| 26  | `[BR-AN-41]`  | `[ ]` | `parse_periodo()` extrae `(año, numero, prefijo)` — `PeriodoData` completo                    |

### 1.7 Deduplicación y persistencia

| #   | Regla          | Check | Verificación                                                |
| --- | -------------- | ----- | ----------------------------------------------------------- |
| 27  | `[BR-PROC-30]` | `[ ]` | Dedup por SHA-256. Mismo hash → HTTP 409 Conflict           |
| 28  | `[BR-PROC-31]` | `[ ]` | Dedup a nivel de archivo binario, no de contenido semántico |
| 29  | `[BR-PROC-40]` | `[ ]` | Persistencia transaccional con savepoint — todo o nada      |
| 30  | `[BR-PROC-41]` | `[ ]` | JSON completo del parser guardado en `datos_completos`      |

---

## 2. Base de datos (`[BR-BE-10]`, `[BR-CONS-*]`)

### 2.1 Schema de evaluaciones

| #   | Regla         | Check | Verificación                                                                        |
| --- | ------------- | ----- | ----------------------------------------------------------------------------------- |
| 31  | `[BR-MOD-04]` | `[ ]` | Columna `modalidad` VARCHAR(20) NOT NULL indexada                                   |
| 32  | `[BR-BE-10]`  | `[ ]` | Índice `ix_evaluaciones_modalidad` existe                                           |
| 33  | `[BR-BE-10]`  | `[ ]` | Índice compuesto `ix_evaluaciones_modalidad_periodo` existe                         |
| 34  | —             | `[ ]` | Índice compuesto `ix_evaluaciones_modalidad_año_orden` existe                       |
| 35  | —             | `[ ]` | CHECK constraint: `modalidad IN ('CUATRIMESTRAL', 'MENSUAL', 'B2B', 'DESCONOCIDA')` |
| 36  | —             | `[ ]` | CHECK constraint: `año >= 2020`                                                     |
| 37  | —             | `[ ]` | CHECK constraint: `puntaje_general IS NULL OR (0 ≤ puntaje_general ≤ 100)`          |

### 2.2 Tipos de datos

| #   | Regla        | Check | Verificación                                         |
| --- | ------------ | ----- | ---------------------------------------------------- |
| 38  | `[BR-BE-11]` | `[ ]` | `puntaje_general`: `NUMERIC(5,2)`                    |
| 39  | `[BR-BE-11]` | `[ ]` | `sent_score`: `NUMERIC(3,2)` (rango `[-1.00, 1.00]`) |
| 40  | `[BR-BE-11]` | `[ ]` | Campos `pct_*`: `NUMERIC(5,2)`                       |

### 2.3 Integridad referencial

| #   | Regla          | Check | Verificación                                                               |
| --- | -------------- | ----- | -------------------------------------------------------------------------- |
| 41  | `[BR-CONS-10]` | `[ ]` | FK `comentario_analisis.evaluacion_id` → `evaluaciones.id` CASCADE DELETE  |
| 42  | `[BR-CONS-11]` | `[ ]` | FK `evaluacion_dimension.evaluacion_id` → `evaluaciones.id` CASCADE DELETE |
| 43  | `[BR-CONS-11]` | `[ ]` | FK `evaluacion_curso.evaluacion_id` → `evaluaciones.id` CASCADE DELETE     |
| 44  | `[BR-CONS-12]` | `[ ]` | FK `evaluaciones.documento_id` → `documentos.id` CASCADE DELETE            |

### 2.4 FSMs de estado

| #   | Regla     | Check | Verificación                                                        |
| --- | --------- | ----- | ------------------------------------------------------------------- |
| 45  | §2.2      | `[ ]` | `Documento.estado`: `subido → procesando → procesado \| error`      |
| 46  | §2.2      | `[ ]` | `Evaluacion.estado`: `pendiente → procesando → completado \| error` |
| 47  | `[AL-50]` | `[ ]` | `Alerta.estado`: `activa → revisada → resuelta \| descartada`       |

---

## 3. Backend — Servicios y API (`[BR-BE-*]`, `[BR-AN-*]`)

### 3.1 Aislamiento por modalidad

| #   | Regla         | Check | Verificación                                                         |
| --- | ------------- | ----- | -------------------------------------------------------------------- |
| 48  | `[BR-MOD-02]` | `[ ]` | Ninguna query analítica mezcla datos de distintas modalidades        |
| 49  | `[BR-AN-01]`  | `[ ]` | Todo cálculo de promedios, rankings, tendencias filtra por modalidad |
| 50  | `[BR-BE-30]`  | `[ ]` | Toda query incluye `WHERE modalidad = :modalidad`                    |
| 51  | `[BR-BE-31]`  | `[ ]` | Endpoints API aceptan `modalidad` como query param                   |
| 52  | `[BR-AN-12]`  | `[ ]` | Solo evaluaciones con `estado = 'completado'` participan en cálculos |

### 3.2 Cálculos analíticos

| #   | Regla        | Check | Verificación                                                                       |
| --- | ------------ | ----- | ---------------------------------------------------------------------------------- |
| 53  | `[BR-AN-10]` | `[ ]` | `promedio_global = AVG(puntaje_general) WHERE estado='completado' AND modalidad=X` |
| 54  | `[BR-AN-11]` | `[ ]` | `promedio_docente` filtrado por modalidad y opcionalmente periodo                  |
| 55  | `[BR-AN-20]` | `[ ]` | Rankings particionados por modalidad — `RANK() OVER (PARTITION BY modalidad)`      |
| 56  | `[BR-AN-21]` | `[ ]` | Desempate en ranking: `evaluaciones_count DESC`                                    |
| 57  | `[BR-AN-30]` | `[ ]` | Tendencias = evolución de promedio por periodos sucesivos de MISMA modalidad       |

### 3.3 Ordenamiento cronológico

| #   | Regla        | Check | Verificación                                                        |
| --- | ------------ | ----- | ------------------------------------------------------------------- |
| 58  | `[BR-AN-40]` | `[ ]` | Sort key: `(año ASC, prefijo ASC, numero ASC)` — no lexicográfico   |
| 59  | `[BR-AN-40]` | `[ ]` | `sort_periodos()` aplicado post-fetch, no `ORDER BY periodo` en SQL |
| 60  | `[BR-AN-42]` | `[ ]` | Continuidad cross-year: `C3 2024 → C1 2025` funciona correctamente  |
| 61  | —            | `[ ]` | Periodos imparseable van al final `(9999, raw, 0)`                  |

### 3.4 DESCONOCIDA

| #   | Regla         | Check | Verificación                                                                           |
| --- | ------------- | ----- | -------------------------------------------------------------------------------------- |
| 62  | `[BR-MOD-05]` | `[ ]` | Evaluaciones DESCONOCIDA se procesan pero se excluyen de rankings, tendencias, alertas |
| 63  | —             | `[ ]` | `_ALERTABLE_MODALIDADES` no incluye DESCONOCIDA                                        |

### 3.5 Enriquecimiento IA (Gemini)

| #   | Regla            | Check | Verificación                                                                                   |
| --- | ---------------- | ----- | ---------------------------------------------------------------------------------------------- |
| 64  | `[BR-ENRICH-01]` | `[ ]` | Fallo de Gemini no impide procesamiento del documento                                          |
| 65  | `[BR-ENRICH-02]` | `[ ]` | Solo se procesan comentarios con `procesado_ia = False`                                        |
| 66  | `[BR-ENRICH-03]` | `[ ]` | Batch size = 10 comentarios por llamada                                                        |
| 67  | `[BR-ENRICH-04]` | `[ ]` | Respuesta de Gemini validada: tema ∈ 10 válidos, sentimiento ∈ 4 válidos, sent_score ∈ [-1, 1] |
| 68  | `[BR-ENRICH-05]` | `[ ]` | Parámetros: `gemini-2.5-flash`, temp=0.3, max_tokens=1024, timeout=30s                         |
| 69  | `[BR-CLAS-12]`   | `[ ]` | Tras IA exitosa: `tema_confianza = "gemini"`, `procesado_ia = True`                            |

### 3.6 Cache

| #   | Regla        | Check | Verificación                                                         |
| --- | ------------ | ----- | -------------------------------------------------------------------- |
| 70  | `[BR-BI-50]` | `[ ]` | TTL del cache de analytics = 300 segundos (5 min)                    |
| 71  | `[BR-BI-51]` | `[ ]` | Clave de cache incluye: `{endpoint}:{modalidad}:{periodo}:{filtros}` |
| 72  | `[BR-BE-32]` | `[ ]` | Modalidad siempre presente en clave de cache                         |
| 73  | `[BR-BI-52]` | `[ ]` | Nuevo documento procesado → invalidar cache de su modalidad          |

### 3.7 Seguridad y rate limiting

| #   | Regla        | Check | Verificación                                                                                        |
| --- | ------------ | ----- | --------------------------------------------------------------------------------------------------- |
| 74  | `[BR-BE-40]` | `[ ]` | Rate limiting en endpoint de consultas IA                                                           |
| 75  | `[BR-BE-41]` | `[ ]` | Llamadas a Gemini registradas en `GeminiAuditLog` (operation, prompt_hash, status, tokens, latency) |
| 76  | `[BR-BE-42]` | `[ ]` | Headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`             |

---

## 4. Frontend (`[BR-FE-*]`, `[VZ-*]`)

### 4.1 Selector de modalidad

| #   | Regla        | Check | Verificación                                                                      |
| --- | ------------ | ----- | --------------------------------------------------------------------------------- |
| 77  | `[BR-FE-01]` | `[ ]` | Selector de modalidad es el primer filtro visible en todas las vistas de análisis |
| 78  | `[BR-FE-02]` | `[ ]` | Opciones: `CUATRIMESTRAL`, `MENSUAL`, `B2B` — `DESCONOCIDA` NO aparece            |
| 79  | `[BR-FE-03]` | `[ ]` | Cambio de modalidad → limpiar filtros → re-fetch → recargar datos                 |
| 80  | `[VZ-03]`    | `[ ]` | AbortController cancela request anterior al cambiar modalidad                     |
| 81  | `[BR-FE-10]` | `[ ]` | Modalidad activa visible en la UI (badge, header, breadcrumb)                     |

### 4.2 Tipos y contratos

| #   | Regla | Check | Verificación                                                                   |
| --- | ----- | ----- | ------------------------------------------------------------------------------ |
| 82  | —     | `[ ]` | `type Modalidad = "CUATRIMESTRAL" \| "MENSUAL" \| "B2B"` — sin DESCONOCIDA     |
| 83  | —     | `[ ]` | `type ModalidadConDesconocida = Modalidad \| "DESCONOCIDA"` — solo uso interno |
| 84  | —     | `[ ]` | `isModalidad()` type guard valida antes de aceptar input de usuario            |
| 85  | —     | `[ ]` | No hay casts `as Modalidad` sin validación previa                              |

### 4.3 Ordenamiento temporal

| #   | Regla     | Check | Verificación                                                       |
| --- | --------- | ----- | ------------------------------------------------------------------ |
| 86  | `[VZ-20]` | `[ ]` | Gráficos temporales usan `sortByPeriodo()` — no sort lexicográfico |
| 87  | `[VZ-21]` | `[ ]` | Labels del eje X legibles: `"C1 2025"`, `"M3 2026"`                |
| 88  | —         | `[ ]` | Re-sort defensivo aplicado tras fetch en hooks                     |

### 4.4 Alertas

| #   | Regla        | Check | Verificación                                                                       |
| --- | ------------ | ----- | ---------------------------------------------------------------------------------- |
| 89  | `[BR-FE-20]` | `[ ]` | Orden: severidad `alta → media → baja`, luego puntaje ASC, luego nombre alfabético |
| 90  | `[BR-FE-21]` | `[ ]` | Badge alta=`destructive`, media=`warning`/amber, baja=`secondary`/muted            |
| 91  | `[BR-FE-22]` | `[ ]` | Conteo de alertas activas visible en KPI card                                      |
| 92  | `[VZ-30]`    | `[ ]` | Homepage muestra alertas `alta` + `activa` ordenadas por puntaje ASC               |

### 4.5 Colores estándar

| #   | Regla     | Check | Verificación                                                                     |
| --- | --------- | ----- | -------------------------------------------------------------------------------- |
| 93  | `[VZ-50]` | `[ ]` | Sentimiento: positivo=green-500, negativo=red-500, mixto=amber-500, neutro=muted |
| 94  | `[VZ-51]` | `[ ]` | Severidad: alta=destructive/rojo, media=amber-500, baja=muted                    |
| 95  | —         | `[ ]` | Colores vienen de `business-rules.ts`, no hardcodeados en componentes            |

### 4.6 Estados de carga

| #   | Regla     | Check | Verificación                                                    |
| --- | --------- | ----- | --------------------------------------------------------------- |
| 96  | `[VZ-40]` | `[ ]` | Estado **Loading**: skeleton animado con placeholders pulsantes |
| 97  | `[VZ-40]` | `[ ]` | Estado **Error**: mensaje + botón "Reintentar"                  |
| 98  | `[VZ-40]` | `[ ]` | Estado **Empty**: mensaje explicativo + CTA (ej: "Suba un PDF") |
| 99  | `[VZ-40]` | `[ ]` | Estado **Data**: contenido normal renderizado                   |

### 4.7 Responsive

| #   | Regla        | Check | Verificación                           |
| --- | ------------ | ----- | -------------------------------------- |
| 100 | `[BR-FE-40]` | `[ ]` | `< 640px`: 1 columna                   |
| 101 | `[BR-FE-40]` | `[ ]` | `640–1024px`: 2 columnas               |
| 102 | `[BR-FE-40]` | `[ ]` | `> 1024px`: 4 cols KPIs, 2 cols charts |

### 4.8 Componentes requeridos

| #   | Regla        | Check | Verificación                                                 |
| --- | ------------ | ----- | ------------------------------------------------------------ |
| 103 | `[BR-FE-30]` | `[ ]` | `ModalidadSelector` — filtro en todas las vistas de análisis |
| 104 | `[BR-FE-30]` | `[ ]` | `KpiCard` — tarjeta con icono, label, valor                  |
| 105 | `[BR-FE-30]` | `[ ]` | `AlertasSection` — lista con badges de severidad             |
| 106 | `[BR-FE-30]` | `[ ]` | `TendenciaChart` — gráfico de área temporal                  |
| 107 | `[BR-FE-30]` | `[ ]` | `DashboardSkeleton` / `DashboardEmpty` / `DashboardError`    |

---

## 5. Analytics y BI (`[BR-BI-*]`, `[BR-AN-50]`)

### 5.1 Tendencias

| #   | Regla        | Check | Verificación                                                                 |
| --- | ------------ | ----- | ---------------------------------------------------------------------------- |
| 108 | `[BR-BI-01]` | `[ ]` | Serie temporal de `AVG(puntaje_general)` por periodo, agrupada por modalidad |
| 109 | `[BR-BI-10]` | `[ ]` | Variación solo entre periodos consecutivos de misma modalidad                |
| 110 | `[BR-AN-32]` | `[ ]` | `variacion_pct = ((actual - anterior) / anterior) * 100`                     |

### 5.2 Análisis cualitativo

| #   | Regla        | Check | Verificación                                                                         |
| --- | ------------ | ----- | ------------------------------------------------------------------------------------ |
| 111 | `[BR-AN-50]` | `[ ]` | `pct_sentimiento = (count_sentimiento / total) * 100`                                |
| 112 | `[BR-AN-51]` | `[ ]` | Top N temas (default 10)                                                             |
| 113 | `[BR-AN-52]` | `[ ]` | Nube de palabras: max 2000 textos, max 60 palabras, min 3 chars, stopwords filtrados |
| 114 | `[BR-AN-53]` | `[ ]` | Análisis cualitativos filtrados por modalidad                                        |

### 5.3 Outliers

| #   | Regla        | Check | Verificación                                               |
| --- | ------------ | ----- | ---------------------------------------------------------- |
| 115 | `[BR-BI-20]` | `[ ]` | Outlier si `\|promedio - media\| > 2σ` dentro de modalidad |
| 116 | `[BR-BI-22]` | `[ ]` | Outliers señalizados en UI pero NO excluidos de cálculos   |

### 5.4 Cobertura IA

| #   | Regla        | Check | Verificación                                                      |
| --- | ------------ | ----- | ----------------------------------------------------------------- |
| 117 | `[BR-BI-40]` | `[ ]` | `cobertura_ia = count(procesado_ia=True) / total * 100` trackeado |
| 118 | `[BR-BI-41]` | `[ ]` | Métrica de cobertura visible en dashboard ejecutivo               |

---

## 6. Alertas (`[AL-*]`)

### 6.1 Alcance temporal

| #   | Regla     | Check | Verificación                                                       |
| --- | --------- | ----- | ------------------------------------------------------------------ |
| 119 | `[AL-01]` | `[ ]` | Alertas generadas con los 2 últimos periodos de la modalidad       |
| 120 | `[AL-02]` | `[ ]` | Un solo periodo → alertas por umbrales absolutos (sin comparación) |
| 121 | `[AL-03]` | `[ ]` | No se mezclan periodos de distintas modalidades                    |

### 6.2 Granularidad y contenido

| #   | Regla     | Check | Verificación                                                                                                                                                |
| --- | --------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 122 | `[AL-10]` | `[ ]` | Unidad mínima: `docente + curso + periodo + modalidad`                                                                                                      |
| 123 | `[AL-30]` | `[ ]` | Alerta contiene: docente_nombre, curso, periodo, modalidad, tipo_alerta, metrica_afectada, valor_actual, valor_anterior, descripcion, severidad, created_at |

### 6.3 Detector: Bajo desempeño `[AL-20]`

| #   | Regla     | Check | Verificación                                                   |
| --- | --------- | ----- | -------------------------------------------------------------- |
| 124 | `[AL-20]` | `[ ]` | `puntaje < 60.0` → severidad **alta**                          |
| 125 | `[AL-20]` | `[ ]` | `puntaje < 70.0` → severidad **media**                         |
| 126 | `[AL-20]` | `[ ]` | `puntaje < 80.0` → severidad **baja**                          |
| 127 | —         | `[ ]` | Constantes: `ALERT_THRESHOLD_HIGH=60.0, MEDIUM=70.0, LOW=80.0` |

### 6.4 Detector: Caída `[AL-21]`

| #   | Regla     | Check | Verificación                                                    |
| --- | --------- | ----- | --------------------------------------------------------------- |
| 128 | `[AL-21]` | `[ ]` | `caída > 15 pts` → **alta**                                     |
| 129 | `[AL-21]` | `[ ]` | `caída > 10 pts` → **media**                                    |
| 130 | `[AL-21]` | `[ ]` | `caída > 5 pts` → **baja**                                      |
| 131 | —         | `[ ]` | `caída = promedio_anterior - promedio_actual` (misma modalidad) |

### 6.5 Detector: Sentimiento `[AL-22]`

| #   | Regla     | Check | Verificación                             |
| --- | --------- | ----- | ---------------------------------------- |
| 132 | `[AL-22]` | `[ ]` | Incremento negativos `> 20%` → **alta**  |
| 133 | `[AL-22]` | `[ ]` | Incremento negativos `> 10%` → **media** |
| 134 | `[AL-22]` | `[ ]` | Incremento negativos `> 5%` → **baja**   |

### 6.6 Detector: Patrón `[AL-23]`

| #   | Regla     | Check | Verificación                         |
| --- | --------- | ----- | ------------------------------------ |
| 135 | `[AL-23]` | `[ ]` | `> 50%` mejoras negativas → **alta** |
| 136 | `[AL-23]` | `[ ]` | `> 30%` actitud negativa → **media** |
| 137 | `[AL-23]` | `[ ]` | `> 40%` tema `otro` → **baja**       |

### 6.7 Deduplicación y ciclo de vida

| #   | Regla     | Check | Verificación                                                                            |
| --- | --------- | ----- | --------------------------------------------------------------------------------------- |
| 138 | `[AL-40]` | `[ ]` | Unicidad: `(docente_nombre, curso, periodo, tipo_alerta)` — upsert, no insert duplicado |
| 139 | `[AL-50]` | `[ ]` | FSM: `activa → revisada → resuelta \| descartada`                                       |
| 140 | —         | `[ ]` | API PATCH `/{id}/estado` valida transiciones permitidas                                 |

---

## 7. Gráficos y visualización (`[VZ-*]`)

### 7.1 Gráficos temporales

| #   | Regla        | Check | Verificación                                                      |
| --- | ------------ | ----- | ----------------------------------------------------------------- |
| 141 | `[VZ-20]`    | `[ ]` | Eje X en orden cronológico `[BR-AN-40]`, no lexicográfico         |
| 142 | `[VZ-21]`    | `[ ]` | Labels: strings originales legibles (`"C1 2025"`, `"M3 2026"`)    |
| 143 | `[BR-FE-11]` | `[ ]` | Gráficos de tendencia NO combinan series de distintas modalidades |
| 144 | —            | `[ ]` | Array del chart ya viene pre-sorted desde el hook                 |

### 7.2 Dashboards requeridos

| #   | Regla     | Check | Verificación                                                                      |
| --- | --------- | ----- | --------------------------------------------------------------------------------- |
| 145 | `[VZ-10]` | `[ ]` | **Ejecutivo**: KPIs, alertas, tendencia, top/bottom, insights, actividad reciente |
| 146 | `[VZ-10]` | `[ ]` | **Estadístico**: promedios, dimensiones (radar), evolución temporal, ranking      |
| 147 | `[VZ-10]` | `[ ]` | **Sentimiento**: distribución, temas, nube de palabras, tabla de comentarios      |
| 148 | `[VZ-10]` | `[ ]` | **Consultas IA**: pregunta-respuesta con evidencia RAG                            |

### 7.3 Alertas en homepage

| #   | Regla     | Check | Verificación                                           |
| --- | --------- | ----- | ------------------------------------------------------ |
| 149 | `[VZ-30]` | `[ ]` | KPI card con conteo de alertas activas                 |
| 150 | `[VZ-30]` | `[ ]` | Lista de alertas alta + activa, por puntaje ASC        |
| 151 | `[VZ-31]` | `[ ]` | Orden visual: `alta → media → baja`, luego puntaje ASC |

---

## 8. Tests

### 8.1 Parser

| #   | Check | Verificación                                                     |
| --- | ----- | ---------------------------------------------------------------- |
| 152 | `[ ]` | Test extracción de header con campos fatales y opcionales        |
| 153 | `[ ]` | Test extracción de dimensiones (5 conocidas, 3 fuentes cada una) |
| 154 | `[ ]` | Test cálculo de resumen cuando falta en PDF                      |
| 155 | `[ ]` | Test descarte de ruido en comentarios (`"."`, `"n/a"`, etc.)     |
| 156 | `[ ]` | Test truncado de comentarios > 10,000 chars                      |
| 157 | `[ ]` | Test clasificación por tema (10 temas, first-match)              |
| 158 | `[ ]` | Test clasificación de sentimiento (4 valores + prior por tipo)   |
| 159 | `[ ]` | Test deduplicación SHA-256 (PDF duplicado → 409)                 |

### 8.2 Modalidad y periodos

| #   | Check | Verificación                                                              |
| --- | ----- | ------------------------------------------------------------------------- |
| 160 | `[ ]` | Test `determinar_modalidad()` para cada regex + DESCONOCIDA               |
| 161 | `[ ]` | Test `parse_periodo()` para C, M, MT, B2B, inválidos                      |
| 162 | `[ ]` | Test `normalizar_periodo()` con variantes de formato                      |
| 163 | `[ ]` | Test `sort_periodos()` intra-año, cross-year, imparseable al final        |
| 164 | `[ ]` | Test frontend `parsePeriodoKey()`, `comparePeriodos()`, `sortByPeriodo()` |

### 8.3 Alertas

| #   | Check | Verificación                                              |
| --- | ----- | --------------------------------------------------------- |
| 165 | `[ ]` | Test BajoDesempenoDetector con umbrales 60/70/80          |
| 166 | `[ ]` | Test CaidaDetector con umbrales 15/10/5                   |
| 167 | `[ ]` | Test SentimientoDetector con umbrales 20/10/5             |
| 168 | `[ ]` | Test PatronDetector con umbrales 50%/30%/40%              |
| 169 | `[ ]` | Test deduplicación `ON CONFLICT` — upsert sin duplicados  |
| 170 | `[ ]` | Test ciclo de vida FSM (transiciones válidas e inválidas) |
| 171 | `[ ]` | Test exclusión de DESCONOCIDA del engine                  |

### 8.4 Analytics

| #   | Check | Verificación                                          |
| --- | ----- | ----------------------------------------------------- |
| 172 | `[ ]` | Test promedios filtrados por modalidad                |
| 173 | `[ ]` | Test rankings particionados por modalidad             |
| 174 | `[ ]` | Test tendencias con orden cronológico correcto        |
| 175 | `[ ]` | Test cálculo de variación entre periodos consecutivos |

### 8.5 Frontend

| #   | Check | Verificación                                                           |
| --- | ----- | ---------------------------------------------------------------------- |
| 176 | `[ ]` | Test `isModalidad()` — acepta 3 válidas, rechaza DESCONOCIDA           |
| 177 | `[ ]` | Test `modalidadFromPeriodo()` — infiere correctamente + fallback       |
| 178 | `[ ]` | Test `severidadClasses()` / `severidadBadgeVariant()` para 3 niveles   |
| 179 | `[ ]` | Test `sentimientoColor()` / `sentimientoTextClass()` para 4 valores    |
| 180 | `[ ]` | Test `MODALIDADES` tiene exactamente 3 entries                         |
| 181 | `[ ]` | Test command-center: skeleton, error, empty, data states               |
| 182 | `[ ]` | Test command-center: ModalidadSelector renderiza 4 botones (Todas + 3) |
| 183 | `[ ]` | Test responsive breakpoints                                            |

### 8.6 Enriquecimiento IA

| #   | Check | Verificación                                                             |
| --- | ----- | ------------------------------------------------------------------------ |
| 184 | `[ ]` | Test Gemini best-effort — fallo no bloquea procesamiento                 |
| 185 | `[ ]` | Test validación de respuesta Gemini (tema, sentimiento, score inválidos) |
| 186 | `[ ]` | Test batch size = 10                                                     |
| 187 | `[ ]` | Test `procesado_ia = True` y `tema_confianza = "gemini"` tras éxito      |

### 8.7 Integración

| #   | Check | Verificación                                                           |
| --- | ----- | ---------------------------------------------------------------------- |
| 188 | `[ ]` | Test pipeline completo: PDF → parser → persistencia → analytics        |
| 189 | `[ ]` | Test API alertas: GET list + GET summary + POST rebuild + PATCH estado |
| 190 | `[ ]` | Test cache: hit, miss, invalidación tras nuevo documento               |

---

## Guía de uso

### En PR reviews

1. Identificar qué área toca el PR (parser, frontend, alertas, etc.)
2. Revisar los checks de esa sección
3. Verificar que no se viola `[BR-MOD-02]` (aislamiento de modalidades)
4. Verificar que nuevas queries incluyen filtro de modalidad
5. Verificar que nuevos datos temporales usan `sort_periodos()` / `sortByPeriodo()`

### En QA manual

1. Subir un PDF de cada modalidad (CUATRIMESTRAL, MENSUAL, B2B)
2. Verificar que el selector de modalidad filtra correctamente
3. Verificar orden cronológico en gráficos de tendencia
4. Verificar alertas: que aparezcan solo para la modalidad seleccionada
5. Verificar estados de carga: loading → data / error / empty
6. Verificar responsive en 3 breakpoints

### Red flags en code review

```
🚩 SELECT ... FROM evaluaciones WHERE periodo = ...  (sin filtro de modalidad)
🚩 ORDER BY periodo                                   (sort lexicográfico)
🚩 as Modalidad                                       (cast sin validación)
🚩 cache_key sin modalidad                            (contaminación cross-modalidad)
🚩 try/except: pass                                   (fallo silencioso en parser)
🚩 Hardcoded colors/labels                            (debe usar business-rules.ts)
```
