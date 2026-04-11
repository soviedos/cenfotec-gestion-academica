# Plan de Pruebas — Reglas de Negocio

> **Fuente:** `docs/business-rules/evaluation-rules.md` v1.0.0
> **Fecha:** 2026-04-05
> **Cobertura actual:** 331 tests (backend 125+43+34+29+71+9=311, frontend 18+2=20)
> **Nota:** Los tests planificados en la sección 2 ya fueron implementados (`test_business_rules.py`, `business-rules-br.test.ts`)

---

## 1. Resumen de auditoría

| Archivo                           | Tests | Calidad    | Gaps críticos                                      |
| --------------------------------- | ----- | ---------- | -------------------------------------------------- |
| `test_periodo.py`                 | 125   | Fuerte     | —                                                  |
| `test_alert_rules.py`             | 43    | Muy fuerte | —                                                  |
| `test_alert_engine.py`            | 11    | Fuerte     | —                                                  |
| `test_alert_engine_edge_cases.py` | 23    | Fuerte     | Dedup, aislamiento, solo-últimos-2, multi-detector |
| `test_classifier.py`              | 29    | Fuerte     | —                                                  |
| `test_business_rules.py`          | 71    | Fuerte     | Reglas BR-\* end-to-end                            |
| `test_invariants.py`              | 9     | Fuerte     | Invariantes de dominio                             |
| `business-rules.test.ts`          | 18    | Bueno      | `isValidPeriodo`, `modalidadFromPeriodo`           |
| `business-rules-br.test.ts`       | 2     | Moderado   | BR-\* frontend                                     |

---

## 2. Estrategia de testing

### Principios

1. **Boundary Value Analysis** — Cada umbral se prueba en 3 puntos: debajo, exactamente, encima.
2. **Partition Equivalence** — Separar por modalidad (C, M, MT, B2B, DESCONOCIDA).
3. **Cross-concern** — Tests que cruzan módulos (periodo + alertas, modalidad + analytics).
4. **Property-based** — Invariantes que siempre deben cumplirse (sort estabilidad, no-duplicidad).

### Archivos a crear/extender

| Archivo                                         | Estado    | Tests |
| ----------------------------------------------- | --------- | ----- |
| `backend/tests/unit/test_business_rules.py`     | ✅ Creado | 71    |
| `frontend/tests/unit/business-rules-br.test.ts` | ✅ Creado | 2     |

---

## 3. Casos críticos por área

### 3.1 Validación de modalidad `[BR-MOD-01]`–`[BR-MOD-05]`

| #   | Caso                             | Input                 | Expected            |
| --- | -------------------------------- | --------------------- | ------------------- |
| 1   | C fuera de rango → DESCONOCIDA   | `"C4 2025"`           | `DESCONOCIDA`       |
| 2   | M fuera de rango → DESCONOCIDA   | `"M11 2025"`          | `DESCONOCIDA`       |
| 3   | MT fuera de rango → DESCONOCIDA  | `"MT0 2025"`          | `DESCONOCIDA`       |
| 4   | B2B sin separador → DESCONOCIDA  | `"B2BEMPRESA"`        | `DESCONOCIDA`       |
| 5   | Año faltante → DESCONOCIDA       | `"C1"`                | `DESCONOCIDA`       |
| 6   | DESCONOCIDA excluida de alertas  | modalidad=DESCONOCIDA | 0 alertas generadas |
| 7   | DESCONOCIDA excluida de rankings | —                     | No participa en AVG |

### 3.2 Validación de periodo `[BR-AN-41]`

| #   | Caso                       | Input             | Expected                         |
| --- | -------------------------- | ----------------- | -------------------------------- |
| 8   | parse C válido             | `"C2 2025"`       | año=2025, numero=2, prefijo="C"  |
| 9   | parse M boundary           | `"M10 2025"`      | año=2025, numero=10, prefijo="M" |
| 10  | parse MT boundary          | `"MT1 2025"`      | año=2025, numero=1, prefijo="MT" |
| 11  | parse B2B con año embedded | `"B2B-CORP-2025"` | año=2025, prefijo="B2B"          |
| 12  | parse B2B sin año          | `"B2B-CORP-XYZ"`  | año=0                            |

### 3.3 Cálculo de periodo_orden `[BR-AN-40]`

| #   | Caso          | Input          | Expected periodo_orden |
| --- | ------------- | -------------- | ---------------------- |
| 13  | C1            | `"C1 2025"`    | 1                      |
| 14  | C3            | `"C3 2025"`    | 3                      |
| 15  | M1            | `"M1 2025"`    | 1                      |
| 16  | M10           | `"M10 2025"`   | 10                     |
| 17  | B2B siempre 0 | `"B2B-X-2025"` | 0                      |

### 3.4 Orden cronológico `[BR-AN-40]`–`[BR-AN-42]`

| #   | Caso                             | Input                   | Expected                        |
| --- | -------------------------------- | ----------------------- | ------------------------------- |
| 18  | Cross-year cuatrimestral         | `[C1'25, C3'24, C2'25]` | `[C3'24, C1'25, C2'25]`         |
| 19  | Mensual numérico (M2 < M10)      | `[M10, M1, M5]` (2025)  | `[M1, M5, M10]`                 |
| 20  | B2B mixed con C                  | `[B2B-X-2025, C1 2025]` | B2B(año=2025,ord=0) antes de C1 |
| 21  | Imparseable al final             | `["basura", "C1 2025"]` | `["C1 2025", "basura"]`         |
| 22  | M vs MT mismo año (prefijo M<MT) | `[MT1 2025, M1 2025]`   | `[M1 2025, MT1 2025]` (M < MT)  |

### 3.5 Alertas: solo últimos 2 periodos `[AL-01]`

| #   | Caso                         | Periodos disponibles    | Expected                 |
| --- | ---------------------------- | ----------------------- | ------------------------ |
| 23  | Exactamente 2 periodos       | `[C2 2025, C1 2025]`    | Usa ambos                |
| 24  | 3+ periodos → solo últimos 2 | `[C3'24, C1'25, C2'25]` | Solo C1'25 y C2'25       |
| 25  | 1 periodo → solo absolutos   | `[C1 2025]`             | Sin comparación temporal |
| 26  | 0 periodos → skip            | `[]`                    | 0 alertas                |

### 3.6 No duplicidad de alertas `[AL-40]`

| #   | Caso                                 | Expected              |
| --- | ------------------------------------ | --------------------- |
| 27  | Misma alerta 2x → upsert             | 1 registro, no 2      |
| 28  | Mismo docente+curso, distinto tipo   | 2 registros separados |
| 29  | Mismo docente+tipo, distinto periodo | 2 registros separados |

### 3.7 Separación entre modalidades `[BR-MOD-02]`

| #   | Caso                                          | Expected                                      |
| --- | --------------------------------------------- | --------------------------------------------- |
| 30  | Engine procesa CUATRIMESTRAL y MENSUAL aparte | Cada uno tiene sus propios 2 últimos periodos |
| 31  | Alertas de C no aparecen en filtro de M       | Filtro por modalidad retorna 0 cross          |
| 32  | DESCONOCIDA no genera alertas                 | \_ALERTABLE_MODALIDADES la excluye            |

### 3.8 Clasificación: boundaries de sentimiento `[BR-CLAS-20]`

| #   | Caso                             | Score   | Expected     |
| --- | -------------------------------- | ------- | ------------ |
| 33  | score = +0.26                    | 0.26    | positivo     |
| 34  | score = +0.25                    | 0.25    | neutro/mixto |
| 35  | score = -0.26                    | -0.26   | negativo     |
| 36  | score = -0.25                    | -0.25   | neutro/mixto |
| 37  | fortaleza + neg keyword → mixto? | depends | prior test   |

---

## 4. Cobertura mínima recomendada

| Área                    | Cobertura actual | Objetivo | Métrica                                      |
| ----------------------- | ---------------- | -------- | -------------------------------------------- |
| Modalidad validación    | 85%              | 95%      | Todas las branches de `determinar_modalidad` |
| Periodo parsing         | 90%              | 95%      | Todos los prefijos + edge cases              |
| Orden cronológico       | 85%              | 95%      | Cross-year + cross-prefix + B2B              |
| Alert detectors         | 95%              | 98%      | Todos los umbrales ±1 punto                  |
| Alert engine            | 50%              | 85%      | Dedup + isolation + last-2                   |
| Classifier sentimiento  | 70%              | 90%      | Boundary ±0.25 + prior combos                |
| Frontend business-rules | 80%              | 90%      | Out-of-range + case variations               |
