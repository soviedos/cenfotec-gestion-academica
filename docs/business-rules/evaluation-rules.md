# Reglas de Negocio — Evaluaciones Docentes

> **Versión:** 1.0.0  
> **Fecha:** 2026-04-05  
> **Estado:** Vigente  
> **Alcance:** Todas las capas del sistema (parser, backend, frontend, BI)

---

## Tabla de contenidos

1. [Introducción](#1-introducción)
2. [Definiciones clave](#2-definiciones-clave)
3. [Clasificación de modalidades](#3-clasificación-de-modalidades)
4. [Reglas de procesamiento](#4-reglas-de-procesamiento)
5. [Reglas de análisis](#5-reglas-de-análisis)
6. [Reglas de alertas](#6-reglas-de-alertas)
7. [Reglas de visualización](#7-reglas-de-visualización)
8. [Reglas de consistencia de datos](#8-reglas-de-consistencia-de-datos)
9. [Reglas para backend](#9-reglas-para-backend)
10. [Reglas para frontend](#10-reglas-para-frontend)
11. [Reglas para analítica y BI](#11-reglas-para-analítica-y-bi)
12. [Extensibilidad](#12-extensibilidad)
13. [Apéndices](#13-apéndices)

---

## 1. Introducción

### 1.1 Propósito

Este documento define las reglas de negocio que gobiernan **toda** la lógica del sistema de Evaluaciones Docentes. Funciona como la fuente de verdad para:

- procesamiento y validación de datos extraídos de PDFs,
- clasificación y análisis de comentarios cualitativos,
- generación de alertas operativas y académicas,
- cálculos estadísticos y de tendencia,
- visualización en dashboards ejecutivos,
- consistencia transversal de datos.

### 1.2 Audiencia

- Desarrolladores backend y frontend.
- Ingenieros de datos.
- Líderes técnicos encargados de revisión de código.

### 1.3 Convenciones del documento

| Prefijo    | Significado                                                   |
| ---------- | ------------------------------------------------------------- |
| **MUST**   | Obligatorio. El sistema no debe funcionar si se viola.        |
| **SHOULD** | Recomendado. Su omisión debe justificarse documentalmente.    |
| **MAY**    | Opcional. Se implementa a discreción del equipo.              |
| `[BR-XX]`  | Identificador de regla de negocio (Business Rule).            |
| `[AL-XX]`  | Identificador de regla de alerta (Alert Rule).                |
| `[VZ-XX]`  | Identificador de regla de visualización (Visualization Rule). |

---

## 2. Definiciones clave

### 2.1 Glosario

| Término                | Definición                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Evaluación**         | Conjunto de datos cuantitativos y cualitativos extraídos de un PDF de evaluación docente de CENFOTEC.                    |
| **Docente**            | Persona evaluada. Se identifica por `docente_nombre` (extraído del campo "Profesor" del PDF).                            |
| **Periodo**            | Segmento temporal en el que ocurrió la evaluación. Su formato depende de la **modalidad**.                               |
| **Modalidad**          | Clasificación del programa académico que determina la estructura de periodos. Ver sección 3.                             |
| **Dimensión**          | Categoría de evaluación cuantitativa (ej. METODOLOGÍA, Dominio, CUMPLIMIENTO, ESTRATEGIA, GENERAL).                      |
| **Fuente de puntaje**  | Origen de la calificación: **Estudiante**, **Director** o **Autoevaluación**.                                            |
| **Comentario**         | Texto cualitativo asociado a una evaluación. Se clasifica por tipo (fortaleza, mejora, observación), tema y sentimiento. |
| **Tema**               | Categoría temática asignada a un comentario (10 posibles, ver sección 4.4).                                              |
| **Sentimiento**        | Clasificación emocional de un comentario: `positivo`, `negativo`, `mixto`, `neutro`.                                     |
| **Puntaje general**    | Porcentaje ponderado final de una evaluación (0–100). Corresponde al `promedio_general` del `resumen_pct`.               |
| **Curso-grupo**        | Combinación de código de curso + grupo evaluado. Unidad mínima de análisis de desempeño.                                 |
| **Escuela**            | Unidad académica que ofrece el curso (ej. "ESC INFORMÁTICA"). Se extrae de la tabla de cursos del PDF.                   |
| **Recinto**            | Sede física donde se imparte el programa. Se extrae del encabezado del PDF.                                              |
| **Enriquecimiento IA** | Proceso post-clasificación en el que Gemini re-clasifica comentarios para obtener tema y sentimiento de mayor precisión. |

### 2.2 Estados del sistema

#### Estado de documento (`Documento.estado`)

```
subido → procesando → procesado
                    ↘ error
```

| Estado       | Significado                                                     |
| ------------ | --------------------------------------------------------------- |
| `subido`     | PDF recibido y almacenado en MinIO. Pendiente de procesamiento. |
| `procesando` | Pipeline activo: extrayendo datos.                              |
| `procesado`  | Pipeline exitoso: evaluación(es) persistida(s).                 |
| `error`      | Pipeline fallido: ver `error_detalle`.                          |

#### Estado de evaluación (`Evaluacion.estado`)

| Estado       | Significado                                     |
| ------------ | ----------------------------------------------- |
| `pendiente`  | Registro creado, aún no procesado.              |
| `procesando` | Extracción en curso.                            |
| `completado` | Datos cuantitativos y cualitativos disponibles. |
| `error`      | Extracción fallida.                             |

---

## 3. Clasificación de modalidades

### 3.1 Definición de modalidades

`[BR-MOD-01]` Toda evaluación **MUST** pertenecer a exactamente una modalidad. La modalidad se determina a partir del código de periodo extraído del PDF.

#### 3.1.1 Modalidad Cuatrimestral

| Propiedad     | Valor                           |
| ------------- | ------------------------------- |
| Código        | `CUATRIMESTRAL`                 |
| Periodos      | `C1`, `C2`, `C3`                |
| Estructura    | 3 periodos por año              |
| Regex periodo | `^C[1-3]\s+\d{4}$`              |
| Ejemplos      | `C1 2024`, `C2 2025`, `C3 2025` |

#### 3.1.2 Modalidad Mensual

| Propiedad     | Valor                                                |
| ------------- | ---------------------------------------------------- |
| Código        | `MENSUAL`                                            |
| Periodos      | `M1`–`M10`, `MT1`–`MT10`                             |
| Estructura    | Hasta 10 periodos regulares + 10 periodos MT por año |
| Regex periodo | `^M(?:T)?\d{1,2}\s+\d{4}$`                           |
| Ejemplos      | `M1 2026`, `M10 2025`, `MT3 2024`                    |

> **Nota:** `MT` (Modular Técnico) es una subdivisión de la modalidad mensual. Se agrupa bajo la misma modalidad pero se distingue en el código de periodo.

#### 3.1.3 Modalidad B2B

| Propiedad     | Valor                                                              |
| ------------- | ------------------------------------------------------------------ |
| Código        | `B2B`                                                              |
| Periodos      | Definidos por contrato corporativo (formato libre con prefijo B2B) |
| Estructura    | Variable según programa                                            |
| Regex periodo | `^B2B[\s-].+`                                                      |
| Ejemplos      | `B2B-EMPRESA-2025-Q1`, `B2B MICROSOFT 2026`                        |

### 3.2 Regla fundamental de aislamiento de modalidades

`[BR-MOD-02]` Está **PROHIBIDO** mezclar datos de distintas modalidades en cualquiera de las siguientes operaciones:

- Cálculo de métricas y promedios
- Rankings de docentes
- Análisis de tendencia
- Generación de alertas
- Visualización en dashboards
- Consultas IA (RAG)
- Exportación de reportes

**Ejemplo de violación:**

```
❌ SELECT AVG(puntaje_general) FROM evaluaciones
   WHERE periodo IN ('C1 2025', 'M3 2025')
   -- PROHIBIDO: mezcla cuatrimestral con mensual
```

**Ejemplo correcto:**

```
✅ SELECT AVG(puntaje_general) FROM evaluaciones
   WHERE modalidad = 'CUATRIMESTRAL' AND periodo IN ('C1 2025', 'C2 2025')
```

### 3.3 Determinación automática de modalidad

`[BR-MOD-03]` El sistema **MUST** inferir la modalidad a partir del periodo extraído del PDF, según la siguiente lógica (pseudocódigo):

```python
def determinar_modalidad(periodo: str) -> str:
    """Retorna 'CUATRIMESTRAL', 'MENSUAL', 'B2B', o 'DESCONOCIDA'."""
    periodo_upper = periodo.strip().upper()

    # B2B: siempre prioridad (previene falsos positivos)
    if periodo_upper.startswith("B2B"):
        return "B2B"

    # Cuatrimestral: C1, C2, C3
    if re.match(r"^C[1-3]\s+\d{4}$", periodo_upper):
        return "CUATRIMESTRAL"

    # Mensual: M1-M10, MT1-MT10
    if re.match(r"^M(?:T)?\d{1,2}\s+\d{4}$", periodo_upper):
        return "MENSUAL"

    return "DESCONOCIDA"
```

`[BR-MOD-04]` El campo `modalidad` **MUST** persistirse en la tabla `evaluaciones` como columna indexada.

`[BR-MOD-05]` Si `modalidad == 'DESCONOCIDA'`, la evaluación **MUST** procesarse normalmente pero **MUST NOT** incluirse en rankings, tendencias ni alertas automatizadas. Se marca para revisión manual.

---

## 4. Reglas de procesamiento

### 4.1 Pipeline de procesamiento de PDFs

`[BR-PROC-01]` El procesamiento de un PDF sigue este pipeline determinístico:

```
1. Recepción y deduplicación (SHA-256)
2. Almacenamiento en MinIO
3. Extracción de encabezado (header)
4. Extracción de métricas (dimensiones + resumen)
5. Extracción de cursos/grupos
6. Extracción de comentarios
7. Clasificación de comentarios (tema + sentimiento)
8. Persistencia transaccional
9. Enriquecimiento IA (best-effort, async)
10. Determinación de modalidad y periodo normalizado
```

`[BR-PROC-02]` El parser **MUST** ser una función pura determinística: dado el mismo PDF, siempre produce el mismo resultado. No depende de estado externo ni de servicios de red.

`[BR-PROC-03]` El parser **MUST NOT** lanzar excepciones. Retorna un `ParseResult` tipado que contiene `data | None`, `errors: list[ParseError]`, `warnings: list[ParseWarning]` y `metadata: ParseMetadata`.

### 4.2 Reglas de extracción de encabezado

`[BR-PROC-10]` Los siguientes campos son **fatales** si no se encuentran (el PDF no se procesa):

| Campo             | Regex de extracción                      |
| ----------------- | ---------------------------------------- |
| `profesor_nombre` | `Profesor:\s*(.+?)\s*(?:\((\w+)\))?\s*$` |
| `periodo`         | `Evaluaci[oó]n\s+docente:\s*(.+)`        |
| `recinto`         | `Recinto:\s*(.+)`                        |

`[BR-PROC-11]` El campo `profesor_codigo` es **opcional** (se extrae de paréntesis después del nombre).

### 4.3 Reglas de extracción de métricas

`[BR-PROC-20]` Las dimensiones conocidas son: **METODOLOGÍA**, **Dominio**, **CUMPLIMIENTO**, **ESTRATEGIA**, **GENERAL**.

`[BR-PROC-21]` Cada dimensión tiene exactamente 3 fuentes de puntaje:

| Fuente         | Descripción                     |
| -------------- | ------------------------------- |
| Estudiante     | Calificación de los estudiantes |
| Director       | Calificación del director       |
| Autoevaluación | Auto-calificación del docente   |

`[BR-PROC-22]` El formato de puntaje es `"puntos_obtenidos / puntos_máximos"` (regex: `([\d.]+)\s*/\s*([\d.]+)`).

`[BR-PROC-23]` Todos los porcentajes **MUST** estar en el rango `[0, 100]`. Valores fuera de rango generan `ParseWarning`.

`[BR-PROC-24]` Si la fila de resumen (`ResumenPorcentajes`) no se encuentra en el PDF, el sistema **MUST** calcularla como promedio de las dimensiones individuales.

### 4.4 Reglas de clasificación de comentarios

#### 4.4.1 Clasificación por tipo

`[BR-CLAS-01]` Cada comentario se clasifica en exactamente un tipo según su columna de origen en el PDF:

| Columna   | Tipo          | Descripción                      |
| --------- | ------------- | -------------------------------- |
| Columna 0 | `fortaleza`   | Aspecto positivo destacado       |
| Columna 1 | `mejora`      | Área de oportunidad / debilidad  |
| Columna 2 | `observacion` | Comentario neutral / informativo |

#### 4.4.2 Filtrado de ruido

`[BR-CLAS-02]` Los siguientes valores se descartan como ruido (no generan registro):

```
".", "..", "-", "--", "'", "''", "n/a", "na", "no", "ninguna", "ninguno",
"no de momento", "no tengo ninguna", "sin comentarios", "sin comentarios.",
"todo perfecto"
```

`[BR-CLAS-03]` Text máximo por comentario: **10,000 caracteres**. Textos más largos se truncan.

#### 4.4.3 Clasificación por tema

`[BR-CLAS-10]` El sistema asigna un tema mediante coincidencia de palabras clave (**first-match wins**, case-insensitive):

| Tema           | Palabras clave (extracto)                                                                     |
| -------------- | --------------------------------------------------------------------------------------------- |
| `metodologia`  | dinám, método, metodolog, actividad, práctic, ejercicio, taller, didáctic, creativ, innovador |
| `dominio_tema` | dominio, conocimiento, experto, experiencia, sabe, manejo del tema, preparad                  |
| `comunicacion` | explic, clar, comunic, interac, entend, escucha, atenci, pregunt, participac                  |
| `evaluacion`   | nota, examen, exámen, evalua, rúbrica, califica, retroaliment, feedback, prueba, quiz         |
| `puntualidad`  | puntual, hora, tarde, asisten, falt, llega tarde, cumpl, responsab                            |
| `material`     | material, presentaci, plataforma, recurso, slide, diapositiva, document, guía, bibliograf     |
| `actitud`      | amable, respetuos, motiv, disposici, pacien, trato, empat, comprensiv, cordial, agradable     |
| `tecnologia`   | cámara, virtual, zoom, teams, micrófono, herramienta, tecnolog, plataforma virtual, en línea  |
| `organizacion` | organiz, estructur, programa, continu, planific, orden, secuencia, syllabus                   |
| `otro`         | Fallback: se asigna cuando ningún keyword coincide                                            |

`[BR-CLAS-11]` La confianza de clasificación por keyword es siempre `tema_confianza = "regla"`.

`[BR-CLAS-12]` Tras enriquecimiento por Gemini exitoso, la confianza pasa a `tema_confianza = "gemini"` y `procesado_ia = True`.

#### 4.4.4 Clasificación por sentimiento

`[BR-CLAS-20]` El sentimiento se determina mediante un algoritmo de puntaje por keywords:

```
score = (positivos_count - negativos_count) / total_keyword_count

Prior por tipo (se suma al conteo antes de calcular):
  - fortaleza  → +1 a positivos_count
  - mejora     → +1 a negativos_count
  - observacion → sin prior

Clasificación final:
  - "positivo"  : score >  0.25
  - "negativo"  : score < -0.25
  - "mixto"     : ambos conteos > 0 Y score en [-0.25, 0.25]
  - "neutro"    : sin keywords O score en [-0.25, 0.25] sin ambos
```

`[BR-CLAS-21]` El `sent_score` se almacena como float en rango `[-1.0, 1.0]`.

**Keywords positivas** (extracto): excelente, muy bien, bien, bueno, genial, perfecto, destaca, recomiendo, increíble, sobresaliente, impecable, dedicad.

**Keywords negativas** (extracto): malo, terrible, pésim, deficiente, horrible, no explic, confus, desorganizad, impuntual, irrespet, no sabe, aburrido, monóton, no recomiendo.

### 4.5 Reglas de enriquecimiento IA (Gemini)

`[BR-ENRICH-01]` El enriquecimiento IA es **best-effort**: su fallo no impide el procesamiento del documento.

`[BR-ENRICH-02]` Solo se procesan comentarios con `procesado_ia = False`.

`[BR-ENRICH-03]` Tamaño de lote: **10 comentarios** por llamada a la API.

`[BR-ENRICH-04]` Validación de respuesta de Gemini — se rechaza y mantiene el resultado de reglas si:

- `tema` no está en el set de 10 temas válidos.
- `sentimiento` no está en `{positivo, neutro, mixto, negativo}`.
- `sent_score` no es un float en `[-1.0, 1.0]`.

`[BR-ENRICH-05]` Parámetros de Gemini:

- Modelo: `gemini-2.5-flash`
- Temperatura: `0.3` (consistencia sobre creatividad)
- Max output tokens: `1024`
- Timeout: `30,000 ms`

### 4.6 Reglas de deduplicación

`[BR-PROC-30]` Cada PDF se identifica por su hash SHA-256. Si ya existe un documento con el mismo hash, el sistema **MUST** rechazar la carga con HTTP 409 Conflict.

`[BR-PROC-31]` La deduplicación es a nivel de archivo, no de contenido semántico. Dos PDFs con contenido idéntico pero archivos binarios distintos se procesan por separado.

### 4.7 Reglas de persistencia

`[BR-PROC-40]` La persistencia de una evaluación es **transaccional con savepoint**: evaluación, dimensiones, cursos y comentarios se persisten en una sola transacción. Si alguno falla, ninguno se persiste.

`[BR-PROC-41]` El JSON completo del resultado del parser (`datos_completos`) se almacena en la evaluación para reprocesamiento futuro.

---

## 5. Reglas de análisis

### 5.1 Aislamiento por modalidad

`[BR-AN-01]` Todo análisis estadístico **MUST** operar dentro de una sola modalidad. Esto incluye:

- Cálculo de promedios
- Rankings de docentes
- Evolución temporal
- Distribución de dimensiones
- Análisis cualitativo (temas, sentimiento)

### 5.2 Cálculo de promedios

`[BR-AN-10]` El promedio global se calcula como:

```
promedio_global = AVG(puntaje_general)
  WHERE estado = 'completado'
  AND modalidad = <modalidad_seleccionada>
  [AND periodo = <filtro_periodo> si aplica]
```

`[BR-AN-11]` El promedio por docente se calcula como:

```
promedio_docente = AVG(puntaje_general)
  WHERE estado = 'completado'
  AND docente_nombre = <docente>
  AND modalidad = <modalidad>
  [AND periodo = <filtro> si aplica]
```

`[BR-AN-12]` Solo se incluyen evaluaciones con `estado = 'completado'` en los cálculos. Evaluaciones en error, pendientes o procesando se excluyen.

### 5.3 Rankings

`[BR-AN-20]` Los rankings se calculan **por modalidad**:

```
RANK() OVER (
  PARTITION BY modalidad
  ORDER BY AVG(puntaje_general) DESC
)
```

`[BR-AN-21]` Criterios de desempate: si dos docentes tienen el mismo promedio, se ordena por `evaluaciones_count DESC` (mayor número de evaluaciones = mayor confiabilidad estadística).

`[BR-AN-22]` Los rankings **MUST** mostrar la posición relativa dentro de la modalidad, no la posición global.

### 5.4 Tendencias

`[BR-AN-30]` Las tendencias se calculan como la evolución del promedio a lo largo de periodos sucesivos **dentro de la misma modalidad**.

`[BR-AN-31]` El eje X de las tendencias **MUST** respetar el orden cronológico (ver sección 5.5).

`[BR-AN-32]` Cálculo de variación entre periodos:

```
variacion_pct = ((promedio_actual - promedio_anterior) / promedio_anterior) * 100
```

### 5.5 Orden cronológico

`[BR-AN-40]` Todos los datos temporales **MUST** ordenarse por:

1. Año (ascendente)
2. Número de periodo dentro del año (ascendente)

#### Orden cuatrimestral

```
C1 2024 → C2 2024 → C3 2024 → C1 2025 → C2 2025 → C3 2025
```

#### Orden mensual

```
M1 2025 → M2 2025 → ... → M10 2025 → M1 2026
MT1 2025 → MT2 2025 → ... → MT10 2025 → MT1 2026
```

`[BR-AN-41]` La función de parsing de periodo **MUST** extraer:

```python
def parse_periodo(periodo: str) -> tuple[int, int, str]:
    """Retorna (año, numero_periodo, prefijo) para ordenamiento."""
    # Ejemplo: "C2 2025"  → (2025, 2, "C")
    # Ejemplo: "M10 2026" → (2026, 10, "M")
    # Ejemplo: "MT3 2024" → (2024, 3, "MT")
```

`[BR-AN-42]` El ordenamiento **MUST** soportar continuidad entre años. Ejemplo correcto:

```
... C3 2024 → C1 2025 → C2 2025 ...
```

### 5.6 Análisis cualitativo

`[BR-AN-50]` La distribución de sentimiento se calcula como:

```
porcentaje_sentimiento = (count_sentimiento / total_comentarios) * 100
```

`[BR-AN-51]` La distribución de temas se calcula de forma análoga. Solo se incluyen los top N temas (default: 10).

`[BR-AN-52]` La nube de palabras se genera con estas restricciones:

- Máximo **2,000** textos como fuente.
- Máximo **60** palabras en la nube.
- Longitud mínima de palabra: **3** caracteres.
- Se excluyen stop-words en español (ver apéndice A).

`[BR-AN-53]` Los análisis cualitativos deben filtrar por modalidad cuando se aplican filtros de periodo. Si no se selecciona periodo, se aplica la modalidad por defecto del contexto activo.

---

## 6. Reglas de alertas

### 6.1 Alcance temporal

`[AL-01]` Las alertas **MUST** generarse usando exclusivamente los **dos últimos periodos disponibles** de la modalidad correspondiente.

**Ejemplo cuatrimestral (datos disponibles: C1 2024, C2 2024, C3 2024, C1 2025):**

- Periodos para alertas: `C3 2024` y `C1 2025`

**Ejemplo mensual (datos disponibles: M1 2025 a M7 2025):**

- Periodos para alertas: `M6 2025` y `M7 2025`

`[AL-02]` Si solo hay un periodo disponible en la modalidad, se generan alertas basadas en umbrales absolutos (sin comparación temporal).

`[AL-03]` **MUST NOT** mezclar periodos de distintas modalidades para generar alertas.

### 6.2 Granularidad

`[AL-10]` Las alertas se generan a nivel de:

```
docente + curso + periodo + modalidad
```

Esto es la **unidad mínima de alerta**. No se generan alertas agregadas genéricas.

**Ejemplo correcto:**

```json
{
  "docente": "JOAQUIN GUTIERREZ VALLEJOS",
  "curso": "INF-02 Programación I",
  "periodo": "C1 2025",
  "modalidad": "CUATRIMESTRAL",
  "metrica": "puntaje_general",
  "valor_actual": 32.27,
  "valor_anterior": 58.5,
  "descripcion": "Caída de 26.23 puntos en puntaje general respecto a C3 2024",
  "severidad": "alta"
}
```

**Ejemplo incorrecto:**

```json
{
  "descripcion": "El promedio general bajó este periodo"
}
```

### 6.3 Tipos de alerta

#### 6.3.1 Bajo desempeño absoluto

`[AL-20]` Se genera cuando un docente tiene un puntaje por debajo del umbral en un curso-periodo específico.

| Umbral           | Severidad |
| ---------------- | --------- |
| `puntaje < 60.0` | **Alta**  |
| `puntaje < 70.0` | **Media** |
| `puntaje < 80.0` | **Baja**  |

**Constantes del sistema:**

```python
ALERT_THRESHOLD_HIGH   = 60.0   # Severidad alta
ALERT_THRESHOLD_MEDIUM = 70.0   # Severidad media
ALERT_THRESHOLD_LOW    = 80.0   # Severidad baja
```

#### 6.3.2 Caída significativa entre periodos

`[AL-21]` Se genera cuando el puntaje de un docente en un curso cae significativamente respecto al periodo anterior **de la misma modalidad**.

| Caída         | Severidad |
| ------------- | --------- |
| `> 15 puntos` | **Alta**  |
| `> 10 puntos` | **Media** |
| `> 5 puntos`  | **Baja**  |

```python
DROP_THRESHOLD_HIGH   = 15.0
DROP_THRESHOLD_MEDIUM = 10.0
DROP_THRESHOLD_LOW    =  5.0
```

**Cálculo:**

```
caida = promedio_periodo_anterior - promedio_periodo_actual
IF caida > DROP_THRESHOLD → generar alerta con severidad correspondiente
```

#### 6.3.3 Cambio negativo en sentimiento

`[AL-22]` Se genera cuando el porcentaje de comentarios negativos de un docente en un curso aumenta significativamente.

| Incremento negativos | Severidad |
| -------------------- | --------- |
| `> 20%`              | **Alta**  |
| `> 10%`              | **Media** |
| `> 5%`               | **Baja**  |

```
pct_neg_actual   = negativos_count / total_count * 100  (periodo actual)
pct_neg_anterior = negativos_count / total_count * 100  (periodo anterior)
incremento       = pct_neg_actual - pct_neg_anterior
```

#### 6.3.4 Patrones críticos en comentarios

`[AL-23]` Se genera cuando se detectan patrones de alarma en los comentarios cualitativos de un docente-curso-periodo:

| Patrón                                                           | Severidad |
| ---------------------------------------------------------------- | --------- |
| > 50% de comentarios de tipo `mejora` con sentimiento `negativo` | **Alta**  |
| > 30% de comentarios con tema `actitud` y sentimiento `negativo` | **Media** |
| > 40% de comentarios clasificados como `otro` (sin tema claro)   | **Baja**  |

### 6.4 Contenido obligatorio de una alerta

`[AL-30]` Cada alerta **MUST** contener todos estos campos:

| Campo              | Tipo     | Descripción                                                  |
| ------------------ | -------- | ------------------------------------------------------------ |
| `docente_nombre`   | string   | Nombre completo del docente                                  |
| `curso`            | string   | Código y nombre del curso                                    |
| `periodo`          | string   | Periodo de la evaluación                                     |
| `modalidad`        | string   | Modalidad (CUATRIMESTRAL, MENSUAL, B2B)                      |
| `tipo_alerta`      | string   | Código del tipo (BAJO_DESEMPEÑO, CAIDA, SENTIMIENTO, PATRON) |
| `metrica_afectada` | string   | Nombre de la métrica (puntaje_general, pct_negativo, etc)    |
| `valor_actual`     | float    | Valor actual de la métrica                                   |
| `valor_anterior`   | float?   | Valor del periodo anterior (null si primera vez)             |
| `descripcion`      | string   | Texto descriptivo en español                                 |
| `severidad`        | string   | `alta`, `media`, `baja`                                      |
| `created_at`       | datetime | Fecha de generación de la alerta                             |

### 6.5 Regla de no duplicidad

`[AL-40]` No se **MUST NOT** generar alertas duplicadas. La unicidad se define por la combinación:

```
(docente_nombre, curso, periodo, tipo_alerta)
```

Si ya existe una alerta para esa combinación, se actualiza en lugar de crear una nueva.

### 6.6 Ciclo de vida de alertas

`[AL-50]` Las alertas tienen los siguientes estados:

```
activa → revisada → resuelta
              ↘ descartada
```

| Estado       | Significado                                                       |
| ------------ | ----------------------------------------------------------------- |
| `activa`     | Generada por el sistema, pendiente de revisión.                   |
| `revisada`   | Un usuario ha visto la alerta.                                    |
| `resuelta`   | Se tomaron acciones correctivas.                                  |
| `descartada` | Se determinó que no requiere acción (falso positivo o aceptable). |

---

## 7. Reglas de visualización

### 7.1 Separación por modalidad

`[VZ-01]` Los dashboards **MUST** presentar datos separados por modalidad. No se permite un view unificado que mezcle modalidades.

`[VZ-02]` El selector de modalidad **MUST** ser el primer filtro visible y aplicarse antes que cualquier otro filtro (periodo, docente, escuela, etc.).

`[VZ-03]` Al cambiar de modalidad, todos los filtros dependientes **MUST** resetearse y recargarse con valores válidos para la nueva modalidad.

### 7.2 Dashboards requeridos

`[VZ-10]` El sistema **MUST** proveer los siguientes dashboards, cada uno operando dentro de una sola modalidad:

| Dashboard        | Contenido principal                                                                 |
| ---------------- | ----------------------------------------------------------------------------------- |
| **Ejecutivo**    | KPIs globales, alertas activas, tendencia, top/bottom, insights, actividad reciente |
| **Estadístico**  | Promedios por docente, dimensiones (radar), evolución temporal, ranking             |
| **Sentimiento**  | Distribución de sentimiento, temas, nube de palabras, tabla de comentarios          |
| **Consultas IA** | Interfaz de pregunta-respuesta con evidencia RAG                                    |

### 7.3 Orden cronológico en gráficos

`[VZ-20]` Todos los gráficos con eje temporal **MUST** respetar el orden cronológico definido en `[BR-AN-40]`.

`[VZ-21]` El eje X de gráficos de tendencia **MUST** usar labels legibles: `"C1 2025"`, `"M3 2026"`, etc.

### 7.4 Alertas en homepage

`[VZ-30]` El dashboard ejecutivo (homepage, `/inicio`) **MUST** mostrar:

- Conteo de alertas activas como KPI card.
- Lista de las alertas de severidad `alta`, ordenadas por puntaje ascendente.
- Cada alerta debe mostrar: docente, motivo, puntaje actual, badge de severidad.

`[VZ-31]` Las alertas se ordenan: `alta` → `media` → `baja`, y dentro de cada nivel por puntaje ascendente (peor primero).

### 7.5 Estados de carga

`[VZ-40]` Cada sección del dashboard **MUST** manejar 4 estados:

| Estado  | UI                                                        |
| ------- | --------------------------------------------------------- |
| Loading | Skeleton animado (placeholders pulsantes)                 |
| Error   | Mensaje de error + botón "Reintentar"                     |
| Empty   | Mensaje explicativo + enlace a acción (ej: "Suba un PDF") |
| Data    | Contenido normal                                          |

### 7.6 Colores estándar de sentimiento

`[VZ-50]` Los colores de sentimiento **MUST** ser consistentes en toda la aplicación:

| Sentimiento | Color                   | Código hex |
| ----------- | ----------------------- | ---------- |
| Positivo    | Verde (green-500)       | `#22c55e`  |
| Negativo    | Rojo (red-500)          | `#ef4444`  |
| Mixto       | Ámbar (amber-500)       | `#f59e0b`  |
| Neutro      | Gris (muted-foreground) | Tema       |

### 7.7 Colores estándar de severidad

`[VZ-51]` Los colores de severidad para alertas:

| Severidad | Color                     |
| --------- | ------------------------- |
| Alta      | `destructive` (rojo)      |
| Media     | `amber-500` (ámbar)       |
| Baja      | `muted-foreground` (gris) |

---

## 8. Reglas de consistencia de datos

### 8.1 Validación obligatoria

`[BR-CONS-01]` Toda evaluación **MUST** tener los siguientes campos válidos para ser incluida en análisis:

| Campo             | Validación                                                     |
| ----------------- | -------------------------------------------------------------- |
| `modalidad`       | Uno de: `CUATRIMESTRAL`, `MENSUAL`, `B2B`                      |
| `periodo`         | Formato válido según regex de su modalidad                     |
| `año`             | Entero ≥ 2020 y ≤ año_actual + 1                               |
| `docente_nombre`  | No vacío, longitud 2–300 caracteres                            |
| `puntaje_general` | Float en rango [0, 100] o NULL (si parsing falló parcialmente) |
| `estado`          | `completado` (para inclusión en análisis)                      |

`[BR-CONS-02]` Si una evaluación no cumple `[BR-CONS-01]`, **MUST NOT** participar en:

- Rankings
- Promedios
- Tendencias
- Alertas
- Dashboards

Su estado queda como `error` o se marca para revisión.

### 8.2 Integridad referencial

`[BR-CONS-10]` Cada `ComentarioAnalisis` **MUST** referenciar una `Evaluacion` existente (FK con `CASCADE DELETE`).

`[BR-CONS-11]` Cada `EvaluacionDimension` y `EvaluacionCurso` **MUST** referenciar una `Evaluacion` existente (FK con `CASCADE DELETE`).

`[BR-CONS-12]` Cada `Evaluacion` **MUST** referenciar un `Documento` existente (FK con `CASCADE DELETE`).

### 8.3 Coherencia de puntajes

`[BR-CONS-20]` Para cada evaluación completada:

```
puntaje_general ≈ resumen_pct.promedio_general  (tolerancia: ±0.5%)
```

Si la diferencia es mayor, se genera un `ParseWarning`.

`[BR-CONS-21]` Para cada dimensión:

```
pct_promedio ≈ AVERAGE(pct_estudiante, pct_director, pct_autoeval)  (tolerancia: ±1.0%)
```

### 8.4 Coherencia de curso-grupo

`[BR-CONS-30]` Para cada curso-grupo:

```
estudiantes_respondieron ≤ estudiantes_matriculados
```

Si se viola, se genera `ParseWarning` pero se procesa igualmente (dato del PDF).

`[BR-CONS-31]` El código de curso **MUST** contener un guión (ej: `INF-02`). Filas sin guión se descartan (son subtotales o encabezados).

### 8.5 Unicidad temporal

`[BR-CONS-40]` Un mismo docente no debería tener más de una evaluación por curso-grupo-periodo-modalidad. Si se detecta duplicado, se emite warning.

---

## 9. Reglas para backend

### 9.1 Validación en el parser

`[BR-BE-01]` El parser **MUST** validar con schemas Pydantic estrictos (ver `app/application/parsing/schemas.py`):

| Schema             | Validaciones clave                                                |
| ------------------ | ----------------------------------------------------------------- |
| `HeaderData`       | `profesor_nombre`: min=2, max=300. `periodo`: min=2, max=50.      |
| `FuentePuntaje`    | `puntos_obtenidos` ≥ 0. `puntos_maximos` > 0. `porcentaje` 0–100. |
| `DimensionMetrica` | `promedio_general_pct` 0–100.                                     |
| `CursoGrupo`       | `respondieron` ≥ 0, `matriculados` ≥ 0. Código con guión.         |
| `ParsedEvaluacion` | `dimensiones`: min_length=1. `cursos`: min_length=1.              |

### 9.2 Estructura de base de datos

`[BR-BE-10]` La tabla `evaluaciones` **MUST** incluir el campo `modalidad` como columna indexada:

```sql
ALTER TABLE evaluaciones ADD COLUMN modalidad VARCHAR(20) NOT NULL DEFAULT 'DESCONOCIDA';
CREATE INDEX idx_evaluaciones_modalidad ON evaluaciones(modalidad);
CREATE INDEX idx_evaluaciones_modalidad_periodo ON evaluaciones(modalidad, periodo);
```

`[BR-BE-11]` Tipos de datos requeridos para campos numéricos:

| Campo             | Tipo SQL       | Justificación            |
| ----------------- | -------------- | ------------------------ |
| `puntaje_general` | `NUMERIC(5,2)` | Precisión de 2 decimales |
| `sent_score`      | `NUMERIC(3,2)` | Rango [-1.00, 1.00]      |
| `pct_*`           | `NUMERIC(5,2)` | Porcentajes 0.00–100.00  |

### 9.3 Normalización de periodos

`[BR-BE-20]` Cada periodo almacenado **MUST** normalizarse al formato canónico:

```
<PREFIJO><NÚMERO> <AÑO>
```

| Modalidad     | Formato canónico      | Ejemplos                |
| ------------- | --------------------- | ----------------------- |
| Cuatrimestral | `C{1-3} {YYYY}`       | `C1 2025`, `C3 2024`    |
| Mensual       | `M{1-10} {YYYY}`      | `M1 2026`, `M10 2025`   |
| Mensual MT    | `MT{1-10} {YYYY}`     | `MT1 2025`, `MT10 2024` |
| B2B           | `B2B-{IDENTIFICADOR}` | `B2B-EMPRESA-2025-Q1`   |

`[BR-BE-21]` Función de normalización:

```python
def normalizar_periodo(raw: str) -> str:
    """Normaliza variantes del periodo al formato canónico.

    Ejemplos:
      "C1-2025"   → "C1 2025"
      " c2  2024" → "C2 2024"
      "M 3 2026"  → "M3 2026"
    """
    cleaned = re.sub(r"[-_/]", " ", raw.strip()).upper()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned
```

### 9.4 Separación lógica en queries

`[BR-BE-30]` Toda query de análisis **MUST** incluir filtro de modalidad:

```python
# ✅ Correcto
stmt = select(Evaluacion).where(
    Evaluacion.estado == "completado",
    Evaluacion.modalidad == modalidad,
)

# ❌ Incorrecto — mezcla modalidades
stmt = select(Evaluacion).where(
    Evaluacion.estado == "completado",
)
```

`[BR-BE-31]` Los endpoints de la API **MUST** aceptar `modalidad` como query parameter obligatorio o inferirlo del contexto del filtro de periodo.

`[BR-BE-32]` El cache **MUST** incluir la modalidad en la clave:

```python
key = f"analytics:resumen:{modalidad}:{periodo}"
```

### 9.5 Rate limiting y seguridad

`[BR-BE-40]` El endpoint de consultas IA **MUST** tener rate limiting para proteger la cuota de la API de Gemini.

`[BR-BE-41]` Toda llamada a Gemini **MUST** registrarse en `GeminiAuditLog` con: operation, prompt_hash (SHA-256), status, tokens, latency.

`[BR-BE-42]` Los headers de seguridad **MUST** incluir: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`.

---

## 10. Reglas para frontend

### 10.1 Filtro obligatorio de modalidad

`[BR-FE-01]` La UI **MUST** presentar un selector de modalidad como **primer filtro** en todas las vistas de análisis. Este filtro no puede omitirse ni dejarse vacío.

`[BR-FE-02]` Opciones del selector:

```typescript
const MODALIDADES = [
  { value: "CUATRIMESTRAL", label: "Cuatrimestral (C1–C3)" },
  { value: "MENSUAL", label: "Mensual (M1–M10, MT1–MT10)" },
  { value: "B2B", label: "B2B (Corporativos)" },
] as const;
```

`[BR-FE-03]` Al cambiar de modalidad se **MUST**:

1. Limpiar filtros de periodo, docente, curso.
2. Re-solicitar valores de filtros disponibles para la nueva modalidad.
3. Recargar todos los datos del dashboard.

### 10.2 Separación visual

`[BR-FE-10]` Cada dashboard **MUST** mostrar claramente la modalidad activa mediante un indicador visual persistente (badge, texto en header, o breadcrumb).

`[BR-FE-11]` Los gráficos de tendencia **MUST NOT** combinar datos de distintas modalidades en un solo eje o serie.

### 10.3 Jerarquía de alertas

`[BR-FE-20]` Las alertas se muestran en el siguiente orden:

1. Severidad: `alta` → `media` → `baja`
2. Dentro de cada severidad: puntaje ascendente (peor primero)
3. Dentro de mismo puntaje: nombre docente alfabético

`[BR-FE-21]` Visual de alertas por severidad:

| Severidad | Badge variant | Background                               |
| --------- | ------------- | ---------------------------------------- |
| Alta      | `destructive` | `border-destructive/20 bg-destructive/5` |
| Media     | `warning`     | `border-amber-500/20 bg-amber-500/5`     |
| Baja      | `secondary`   | `border-muted bg-muted/5`                |

`[BR-FE-22]` El conteo de alertas activas **MUST** ser visible en el KPI card del dashboard ejecutivo.

### 10.4 Componentes clave requeridos

`[BR-FE-30]` Los siguientes componentes son requeridos:

| Componente          | Uso                                                  |
| ------------------- | ---------------------------------------------------- |
| `ModalidadSelector` | Filtro de modalidad en todas las vistas de análisis  |
| `PeriodFilter`      | Filtro de periodo (opciones según modalidad activa)  |
| `KpiCard`           | Tarjeta de métrica con icono, label, valor           |
| `AlertasSection`    | Lista de alertas con badges de severidad             |
| `TendenciaChart`    | Gráfico de área con evolución temporal               |
| `DocenteList`       | Lista rankeada de docentes (top/bottom)              |
| `InsightsSection`   | Texto auto-generado de insights cualitativos         |
| `ActividadSection`  | Lista de actividad reciente con estados de documento |
| `DashboardSkeleton` | Estado de carga animado                              |
| `DashboardEmpty`    | Estado sin datos con CTA                             |
| `DashboardError`    | Estado de error con retry                            |

### 10.5 Responsive design

`[BR-FE-40]` Los dashboards **MUST** soportar:

| Breakpoint   | Layout                              |
| ------------ | ----------------------------------- |
| `< 640px`    | 1 columna, menú hamburguesa         |
| `640–1024px` | 2 columnas                          |
| `> 1024px`   | 4 columnas para KPIs, 2 para charts |

---

## 11. Reglas para analítica y BI

### 11.1 Cálculo de tendencias

`[BR-BI-01]` La tendencia se calcula como una serie temporal de `promedio_global` por periodo, **agrupada por modalidad**:

```sql
SELECT periodo, AVG(puntaje_general) AS promedio, COUNT(*) AS evaluaciones_count
FROM evaluaciones
WHERE estado = 'completado' AND modalidad = :modalidad
GROUP BY periodo
ORDER BY /* orden cronológico según [BR-AN-40] */
```

`[BR-BI-02]` La tendencia por docente se calcula de forma análoga, filtrando adicionalmente por `docente_nombre`.

### 11.2 Variación entre periodos

`[BR-BI-10]` La variación **MUST** calcularse solo entre periodos consecutivos de la misma modalidad:

```python
def calcular_variacion(
    datos: list[PeriodoMetrica],  # ya ordenados cronológicamente
) -> list[dict]:
    result = []
    for i in range(1, len(datos)):
        anterior = datos[i - 1]
        actual = datos[i]
        variacion_abs = actual.promedio - anterior.promedio
        variacion_pct = (variacion_abs / anterior.promedio * 100) if anterior.promedio > 0 else 0
        result.append({
            "periodo": actual.periodo,
            "promedio": actual.promedio,
            "variacion_abs": round(variacion_abs, 2),
            "variacion_pct": round(variacion_pct, 2),
            "tendencia": "subió" if variacion_abs > 0 else "bajó" if variacion_abs < 0 else "estable",
        })
    return result
```

### 11.3 Identificación de outliers

`[BR-BI-20]` Un docente es outlier **dentro de su modalidad** si su promedio se desvía más de 2 desviaciones estándar de la media:

```
outlier = |promedio_docente - promedio_modalidad| > 2 * stddev_modalidad
```

`[BR-BI-21]` Tipos de outlier:

| Tipo         | Condición                                         |
| ------------ | ------------------------------------------------- |
| Outlier alto | `promedio > media + 2σ` (rendimiento excepcional) |
| Outlier bajo | `promedio < media - 2σ` (rendimiento preocupante) |

`[BR-BI-22]` Los outliers se señalizan en la UI pero no se excluyen de los cálculos.

### 11.4 Integración de sentimiento con métricas cuantitativas

`[BR-BI-30]` Se **SHOULD** calcular un **índice compuesto** para cada docente-curso-periodo:

```
indice_compuesto = (puntaje_cuantitativo * 0.7) + (sentimiento_normalizado * 0.3)

Donde:
  puntaje_cuantitativo = puntaje_general (0–100)
  sentimiento_normalizado = ((avg_sent_score + 1) / 2) * 100
  // Convierte [-1, 1] → [0, 100]
```

`[BR-BI-31]` El sentimiento promedio de un docente se calcula solo con comentarios donde `sentimiento IS NOT NULL`.

### 11.5 Métricas de cobertura IA

`[BR-BI-40]` Se **MUST** trackear el porcentaje de comentarios enriquecidos por IA:

```
cobertura_ia = (count(procesado_ia = True) / total_comentarios) * 100
```

`[BR-BI-41]` Se **SHOULD** mostrar como métrica de sistema en el dashboard ejecutivo.

### 11.6 Caché y rendimiento

`[BR-BI-50]` Los resultados de analytics **MUST** cachearse con TTL de **5 minutos** en Redis.

`[BR-BI-51]` La clave de cache **MUST** incluir: `{endpoint}:{modalidad}:{periodo}:{filtros_adicionales}`.

`[BR-BI-52]` Al procesar un nuevo documento, se **SHOULD** invalidar el cache de la modalidad correspondiente.

---

## 12. Extensibilidad

### 12.1 Nuevas modalidades

`[BR-EXT-01]` Para agregar una nueva modalidad:

1. Agregar regex de detección en `determinar_modalidad()`.
2. Definir el orden cronológico de los periodos.
3. No se requiere cambio en la estructura de base de datos (el campo `modalidad` es VARCHAR).
4. Verificar que los filtros del frontend se actualicen dinámicamente (no hardcodeados).

**Checklist:**

```
[ ] Regex de periodo en determinar_modalidad()
[ ] Función de ordenamiento para la nueva modalidad
[ ] Test unitario de clasificación de periodo
[ ] Test de ordenamiento cronológico
[ ] Registro en MODALIDADES del frontend
[ ] Test e2e de filtrado por modalidad
```

### 12.2 Nuevos tipos de alerta

`[BR-EXT-10]` Para agregar un nuevo tipo de alerta:

1. Definir el tipo en el enum de `tipo_alerta`.
2. Implementar la lógica de detección en el servicio de alertas.
3. Definir umbrales de severidad.
4. Agregar el tipo a la UI de alertas.
5. Agregar test unitario y de integración.

**Contrato mínimo de una alerta:**

```python
class AlertaDocente(BaseModel):
    docente_nombre: str
    curso: str
    periodo: str
    modalidad: str
    tipo_alerta: str       # Enum extensible
    metrica_afectada: str
    valor_actual: float
    valor_anterior: float | None
    descripcion: str
    severidad: Literal["alta", "media", "baja"]
    created_at: datetime
```

### 12.3 Nuevas métricas

`[BR-EXT-20]` Para agregar una nueva métrica de análisis:

1. Agregar el cálculo en el repositorio o servicio correspondiente.
2. Agregar el schema Pydantic de respuesta.
3. Agregar el endpoint API.
4. Agregar el tipo TypeScript en el frontend.
5. Agregar el componente de visualización.
6. **MUST** respetar el aislamiento por modalidad `[BR-MOD-02]`.

### 12.4 Nuevas fuentes de evaluación

`[BR-EXT-30]` Si se agrega una nueva fuente de puntaje (ej: "Evaluación de pares"):

1. Agregar campo en `EvaluacionDimension`.
2. Actualizar el parser para extraer la nueva columna.
3. Actualizar `ResumenPorcentajes`.
4. No se requiere cambio en la lógica de alertas (opera sobre `puntaje_general`).

---

## 13. Apéndices

### Apéndice A: Stop-words español (nube de palabras)

```
el la los las un una unos unas de del al a en con por para su sus
es son fue ser no si lo le se que y o el del más muy como pero
todo toda todos todas este esta estos estas ese esa esos esas
me te nos les mi tu hay ya también entre sobre hasta sin embargo
bien mal mucho poco cuando tiene cada uno era han ha
```

### Apéndice B: Constantes del sistema

| Constante                 | Valor   | Archivo                        |
| ------------------------- | ------- | ------------------------------ |
| `ALERT_THRESHOLD_HIGH`    | `60.0`  | dashboard_service.py           |
| `ALERT_THRESHOLD_MEDIUM`  | `70.0`  | (por implementar)              |
| `ALERT_THRESHOLD_LOW`     | `80.0`  | (por implementar)              |
| `DROP_THRESHOLD_HIGH`     | `15.0`  | (por implementar)              |
| `DROP_THRESHOLD_MEDIUM`   | `10.0`  | (por implementar)              |
| `DROP_THRESHOLD_LOW`      | `5.0`   | (por implementar)              |
| `SENTIMENT_THRESHOLD_POS` | `0.25`  | classification/\_\_init\_\_.py |
| `SENTIMENT_THRESHOLD_NEG` | `-0.25` | classification/\_\_init\_\_.py |
| `GEMINI_BATCH_SIZE`       | `10`    | gemini_enrichment_service.py   |
| `GEMINI_TEMPERATURE`      | `0.3`   | prompt_templates.py            |
| `GEMINI_MAX_TOKENS`       | `1024`  | gemini_gateway.py              |
| `GEMINI_TIMEOUT_MS`       | `30000` | gemini_gateway.py              |
| `CACHE_TTL_SECONDS`       | `300`   | cache.py (5 minutos)           |
| `MAX_COMMENT_LENGTH`      | `10000` | processing_service.py          |
| `WORD_CLOUD_MAX_TEXTS`    | `2000`  | qualitative_repo.py            |
| `WORD_CLOUD_MAX_WORDS`    | `60`    | qualitative_repo.py            |
| `WORD_CLOUD_MIN_LENGTH`   | `3`     | qualitative_repo.py            |
| `RAG_MAX_METRICS`         | `10`    | query_service.py               |
| `RAG_MAX_COMMENTS`        | `20`    | query_service.py               |
| `PAGINATION_DEFAULT_SIZE` | `20`    | api endpoints                  |
| `PAGINATION_MAX_SIZE`     | `100`   | api endpoints                  |

### Apéndice C: Temas válidos para clasificación

```python
TEMAS_VALIDOS = {
    "metodologia",
    "dominio_tema",
    "comunicacion",
    "evaluacion",
    "puntualidad",
    "material",
    "actitud",
    "tecnologia",
    "organizacion",
    "otro",
}
```

### Apéndice D: Sentimientos válidos

```python
SENTIMIENTOS_VALIDOS = {
    "positivo",
    "negativo",
    "mixto",
    "neutro",
}
```

### Apéndice E: Tipos de comentario

```python
TIPOS_COMENTARIO = {
    "fortaleza",
    "mejora",
    "observacion",
}
```

### Apéndice F: Fuentes de evaluación

```python
FUENTES_EVALUACION = {
    "Estudiante",
    "Director",
}
```

---

> **Historial de cambios**
>
> | Versión | Fecha      | Descripción       |
> | ------- | ---------- | ----------------- |
> | 1.0.0   | 2026-04-05 | Documento inicial |
