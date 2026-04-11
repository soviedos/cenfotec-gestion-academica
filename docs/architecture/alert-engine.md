# Motor de Alertas — Documentación Técnica

> **Reglas de negocio:** `[AL-01]` – `[AL-50]`, `[VZ-30]` – `[VZ-31]`  
> **Última actualización:** 2026-04-05  
> **Estado:** Implementado y con tests

---

## 1. Visión general

El motor de alertas detecta anomalías académicas de forma automática, analizando los **dos últimos periodos disponibles** de cada modalidad. Opera como un pipeline de detección puro que se puede ejecutar on-demand o tras procesar un nuevo PDF.

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ AlertEngine │────▶│  Detectors   │────▶│ AlertCandidate│────▶│ Upsert   │
│  .run_all() │     │ (4 plugins)  │     │  (propuestas) │     │ Postgres │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────┘
       │                                        │
       ▼                                        ▼
  Por modalidad:                         Dedup por:
  CUATRIMESTRAL,                    (docente, curso,
  MENSUAL, B2B                      periodo, tipo_alerta)
```

---

## 2. Arquitectura de capas

| Capa                | Archivo                                          | Responsabilidad                           |
| ------------------- | ------------------------------------------------ | ----------------------------------------- |
| **Dominio**         | `app/domain/alert_rules.py`                      | Detectores puros, value objects, umbrales |
| **Dominio**         | `app/domain/entities/alerta.py`                  | Entidad SQLAlchemy + constraints          |
| **Dominio**         | `app/domain/entities/enums.py`                   | `TipoAlerta`, `Severidad`, `AlertaEstado` |
| **Dominio**         | `app/domain/schemas/alertas.py`                  | Schemas Pydantic de respuesta API         |
| **Aplicación**      | `app/application/services/alert_engine.py`       | Orquestador `AlertEngine`                 |
| **Aplicación**      | `app/application/services/alerta_service.py`     | Capa de servicio para la API              |
| **Infraestructura** | `app/infrastructure/repositories/alerta_repo.py` | Queries, upsert, agregaciones             |
| **API**             | `app/api/v1/alertas.py`                          | Endpoints REST                            |
| **Frontend**        | `src/lib/business-rules.ts`                      | Constantes de umbrales, labels, colores   |
| **Frontend**        | `src/types/index.ts`                             | `TipoAlerta`, `Severidad`, `AlertaEstado` |

---

## 3. Detectores

Cada detector implementa el protocolo `AlertDetector` y recibe snapshots pre-agregados del periodo actual y (opcionalmente) del anterior.

### 3.1 Bajo desempeño absoluto `[AL-20]`

**Clase:** `BajoDesempenoDetector`  
**Métrica:** `puntaje_general` de un docente-curso en el periodo actual.

| Condición        | Severidad |
| ---------------- | --------- |
| `puntaje < 60.0` | **alta**  |
| `puntaje < 70.0` | **media** |
| `puntaje < 80.0` | **baja**  |

```python
# Constantes en alert_rules.py
ALERT_THRESHOLD_HIGH   = 60.0
ALERT_THRESHOLD_MEDIUM = 70.0
ALERT_THRESHOLD_LOW    = 80.0
```

**Ejemplo válido:**

```json
{
  "tipo_alerta": "BAJO_DESEMPEÑO",
  "docente_nombre": "JOAQUIN GUTIERREZ",
  "curso": "INF-02 Programación I",
  "periodo": "C1 2025",
  "modalidad": "CUATRIMESTRAL",
  "metrica_afectada": "puntaje_general",
  "valor_actual": 45.2,
  "valor_anterior": null,
  "severidad": "alta",
  "descripcion": "Puntaje 45.20% está por debajo del umbral de 60%"
}
```

### 3.2 Caída significativa `[AL-21]`

**Clase:** `CaidaDetector`  
**Requiere:** Snapshot del periodo anterior.  
**Métrica:** Diferencia de `puntaje_general` entre periodos consecutivos.

| Caída         | Severidad |
| ------------- | --------- |
| `> 15 puntos` | **alta**  |
| `> 10 puntos` | **media** |
| `> 5 puntos`  | **baja**  |

```python
DROP_THRESHOLD_HIGH   = 15.0
DROP_THRESHOLD_MEDIUM = 10.0
DROP_THRESHOLD_LOW    =  5.0
```

**Ejemplo válido:**

```json
{
  "tipo_alerta": "CAIDA",
  "valor_actual": 58.0,
  "valor_anterior": 78.5,
  "severidad": "alta",
  "descripcion": "Caída de 20.50 puntos en puntaje general respecto a C3 2024"
}
```

**Ejemplo inválido — cruza modalidades:**

```
❌ Comparar M5 2025 (MENSUAL) con C3 2024 (CUATRIMESTRAL)
   Viola [AL-03]: MUST NOT mezclar periodos de distintas modalidades
```

### 3.3 Cambio en sentimiento `[AL-22]`

**Clase:** `SentimientoDetector`  
**Requiere:** Snapshot del periodo anterior.  
**Métrica:** Incremento del porcentaje de comentarios negativos.

| Incremento en % negativos | Severidad |
| ------------------------- | --------- |
| `> 20%`                   | **alta**  |
| `> 10%`                   | **media** |
| `> 5%`                    | **baja**  |

**Ejemplo válido:**

```json
{
  "tipo_alerta": "SENTIMIENTO",
  "metrica_afectada": "pct_negativos",
  "valor_actual": 45.0,
  "valor_anterior": 20.0,
  "severidad": "alta",
  "descripcion": "Incremento de 25.00% en comentarios negativos"
}
```

### 3.4 Patrones críticos `[AL-23]`

**Clase:** `PatronDetector`  
**Métrica:** Distribución de comentarios por tipo/tema/sentimiento en el periodo actual.

| Patrón detectado                              | Severidad |
| --------------------------------------------- | --------- |
| > 50% comentarios `mejora` + `negativo`       | **alta**  |
| > 30% comentarios tema `actitud` + `negativo` | **media** |
| > 40% comentarios con tema `otro`             | **baja**  |

---

## 4. Alcance temporal `[AL-01]`

El motor usa exclusivamente los **dos últimos periodos** de cada modalidad. La selección se hace en el repositorio:

```python
# alerta_repo.py :: find_last_two_periods()
SELECT DISTINCT periodo
FROM evaluaciones
WHERE estado = 'completado' AND modalidad = :modalidad
ORDER BY año DESC, periodo_orden DESC
LIMIT 2
```

**Ejemplo cuatrimestral** (datos: C1–C3 2024, C1 2025):

- Periodo actual: `C1 2025`
- Periodo anterior: `C3 2024`

**Ejemplo con un solo periodo:** Si solo existe `C1 2025`, se generan alertas absolutas (sin comparación).

---

## 5. Snapshots pre-agregados

Para evitar N+1 queries, el repositorio carga todos los datos necesarios en una sola consulta:

```python
# alert_rules.py :: DocenteCursoSnapshot
@dataclass(frozen=True, slots=True)
class DocenteCursoSnapshot:
    evaluacion_id: uuid.UUID
    docente_nombre: str
    curso: str
    periodo: str
    modalidad: str
    puntaje_general: float | None  # AVG(puntaje_general)
    total_comentarios: int
    negativos_count: int
    mejora_negativo_count: int
    actitud_negativo_count: int
    otro_count: int
```

**Estructura del resultado:**

```python
{
  "C1 2025": {
    ("JOAQUIN GUTIERREZ", "INF-02 Programación I"): DocenteCursoSnapshot(...),
    ("MARIA LOPEZ", "ISC-01 Redes"): DocenteCursoSnapshot(...),
  },
  "C3 2024": { ... }
}
```

---

## 6. Deduplicación `[AL-40]`

La unicidad se define por la combinación:

```
(docente_nombre, curso, periodo, tipo_alerta, modalidad)
```

### Deduplicación en dos capas

**Capa 1 — In-memory (dentro de `_detect()`):**

Antes de emitir candidatos, el motor mantiene un `set` de tuplas ya vistas para evitar duplicados dentro de la misma ejecución:

```python
seen: set[tuple[str, str, str, str, str]] = set()
dedup_key = (candidate.docente_nombre, candidate.curso,
             candidate.periodo, candidate.tipo_alerta.value,
             candidate.modalidad)
if dedup_key not in seen:
    seen.add(dedup_key)
    candidates.append(candidate)
```

**Capa 2 — Base de datos (`upsert_batch()`):**

El upsert usa `ON CONFLICT … DO UPDATE` de PostgreSQL. Solo se actualizan alertas en `estado = 'activa'`; las que ya fueron revisadas o resueltas se preservan.

**Ejemplo — alerta duplicada ignorada:**

```sql
INSERT INTO alertas (docente_nombre, curso, periodo, tipo_alerta, ...)
VALUES ('JOAQUIN GUTIERREZ', 'INF-02', 'C1 2025', 'BAJO_DESEMPEÑO', ...)
ON CONFLICT (docente_nombre, curso, periodo, tipo_alerta, modalidad) DO UPDATE
SET valor_actual = EXCLUDED.valor_actual, ...
WHERE alertas.estado = 'activa';
-- Si alertas.estado = 'revisada', no se actualiza ✓
```

---

## 7. Ciclo de vida `[AL-50]`

```
activa ──▶ revisada ──▶ resuelta
                   └──▶ descartada
```

| Estado       | Significado                  | Transición permitida       |
| ------------ | ---------------------------- | -------------------------- |
| `activa`     | Generada por el motor        | → `revisada`               |
| `revisada`   | Vista por un usuario         | → `resuelta`, `descartada` |
| `resuelta`   | Acciones correctivas tomadas | — (terminal)               |
| `descartada` | Falso positivo / aceptable   | — (terminal)               |

**Endpoint de transición:**

```
PATCH /api/v1/alertas/{id}/estado
Body: { "estado": "revisada" | "resuelta" | "descartada" }
```

---

## 8. API REST

| Método  | Ruta                          | Descripción                                   |
| ------- | ----------------------------- | --------------------------------------------- |
| `GET`   | `/api/v1/alertas`             | Lista paginada con filtros                    |
| `GET`   | `/api/v1/alertas/summary`     | Resumen: conteos por severidad/tipo/modalidad |
| `POST`  | `/api/v1/alertas/rebuild`     | Re-ejecutar todas las detecciones             |
| `PATCH` | `/api/v1/alertas/{id}/estado` | Transición de estado                          |

### Filtros disponibles en `GET /alertas`

| Parámetro     | Tipo   | Ejemplo             |
| ------------- | ------ | ------------------- |
| `modalidad`   | string | `CUATRIMESTRAL`     |
| `año`         | int    | `2025`              |
| `periodo`     | string | `C1 2025`           |
| `severidad`   | string | `alta`              |
| `estado`      | string | `activa`            |
| `docente`     | string | `JOAQUIN GUTIERREZ` |
| `curso`       | string | `INF-02`            |
| `tipo_alerta` | string | `BAJO_DESEMPEÑO`    |
| `page`        | int    | `1`                 |
| `page_size`   | int    | `20`                |

---

## 9. Impacto en frontend

### 9.1 Tipos TypeScript (`src/types/index.ts`)

```typescript
type TipoAlerta = "BAJO_DESEMPEÑO" | "CAIDA" | "SENTIMIENTO" | "PATRON";
type Severidad = "alta" | "media" | "baja";
type AlertaEstado = "activa" | "revisada" | "resuelta" | "descartada";

interface AlertaResponse {
  id: string;
  docente_nombre: string;
  curso: string;
  periodo: string;
  modalidad: Modalidad;
  tipo_alerta: TipoAlerta;
  valor_actual: number;
  valor_anterior: number | null;
  descripcion: string;
  severidad: Severidad;
  estado: AlertaEstado;
  // ...
}
```

### 9.2 Utilidades (`src/lib/business-rules.ts`)

| Función                    | Uso                                                          |
| -------------------------- | ------------------------------------------------------------ |
| `tipoAlertaLabel(t)`       | `"BAJO_DESEMPEÑO"` → `"Bajo desempeño"`                      |
| `alertaEstadoLabel(e)`     | `"activa"` → `"Activa"`                                      |
| `severidadClasses(s)`      | Tailwind classes para cards/badges                           |
| `severidadBadgeVariant(s)` | Variante Shadcn: `"destructive"`, `"warning"`, `"secondary"` |
| `compareSeveridad(a, b)`   | Comparador: alta < media < baja                              |
| `ALERT_THRESHOLDS`         | Umbrales absolutos (60/70/80)                                |
| `DROP_THRESHOLDS`          | Umbrales de caída (15/10/5)                                  |

### 9.3 Colores de severidad `[VZ-51]`

| Severidad | Background        | Text                    | Border                |
| --------- | ----------------- | ----------------------- | --------------------- |
| **alta**  | `bg-red-500/10`   | `text-red-600`          | `border-red-500/20`   |
| **media** | `bg-amber-500/10` | `text-amber-600`        | `border-amber-500/20` |
| **baja**  | `bg-muted`        | `text-muted-foreground` | `border-border`       |

### 9.4 Orden de presentación `[BR-FE-20]`

1. Severidad: `alta` → `media` → `baja`
2. Dentro de cada severidad: puntaje ascendente (peor primero)
3. Desempate: nombre docente alfabético

---

## 10. Impacto en backend

### 10.1 Entidad y migración

```python
# app/domain/entities/alerta.py
class Alerta(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "alertas"
    # ... campos ...
    __table_args__ = (
        UniqueConstraint("docente_nombre", "curso", "periodo", "tipo_alerta",
                         name="uq_alertas_dedup"),
        CheckConstraint("modalidad IN ('CUATRIMESTRAL','MENSUAL','B2B')"),
        CheckConstraint("severidad IN ('alta','media','baja')"),
        CheckConstraint("estado IN ('activa','revisada','resuelta','descartada')"),
    )
```

### 10.2 Inyección de detectores

El `AlertEngine` acepta detectores inyectables para testing:

```python
engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])
# En producción: usa ALL_DETECTORS (los 4)
```

### 10.3 Extensibilidad `[BR-EXT-10]`

Para agregar un nuevo tipo de alerta:

1. Crear clase que implemente `AlertDetector` en `alert_rules.py`
2. Agregar valor al enum `TipoAlerta`
3. Registrar instancia en `ALL_DETECTORS`
4. Agregar tipo a `TipoAlerta` en frontend (`src/types/index.ts`)
5. Agregar label en `tipoAlertaLabel()` (`src/lib/business-rules.ts`)
6. Crear tests unitarios y de integración

---

## 11. Tests

| Suite          | Archivo                                    | Tests | Cobertura                 |
| -------------- | ------------------------------------------ | ----- | ------------------------- |
| Detectores     | `tests/unit/test_alert_rules.py`           | 68    | 4 detectores + edge cases |
| API            | `tests/api/test_alertas.py`                | 17    | Endpoints + filtros       |
| Frontend       | `tests/components/command-center.test.tsx` | 20    | Renderizado + interacción |
| Business rules | `tests/unit/business-rules.test.ts`        | 36    | Labels, colores, umbrales |

---

## 12. Ejemplos de validación

### ✅ Alerta correcta

```json
{
  "docente_nombre": "JOAQUIN GUTIERREZ VALLEJOS",
  "curso": "INF-02 Programación I",
  "periodo": "C1 2025",
  "modalidad": "CUATRIMESTRAL",
  "tipo_alerta": "CAIDA",
  "metrica_afectada": "puntaje_general",
  "valor_actual": 32.27,
  "valor_anterior": 58.5,
  "descripcion": "Caída de 26.23 puntos en puntaje general respecto a C3 2024",
  "severidad": "alta"
}
```

### ❌ Alerta inválida — cruza modalidades

```json
{
  "periodo": "C1 2025",
  "modalidad": "CUATRIMESTRAL",
  "valor_anterior_periodo": "M5 2025",
  "ERROR": "Compara cuatrimestral con mensual → viola [AL-03]"
}
```

### ❌ Alerta inválida — sin granularidad

```json
{
  "descripcion": "El promedio general bajó este periodo",
  "ERROR": "No identifica docente+curso+periodo → viola [AL-10]"
}
```

### ❌ Alerta inválida — datos insuficientes

```json
{
  "modalidad": "CUATRIMESTRAL",
  "periodos_disponibles": ["C1 2025"],
  "tipo_alerta": "CAIDA",
  "ERROR": "CaidaDetector requiere 2 periodos → sin periodo anterior, no se genera"
}
```
