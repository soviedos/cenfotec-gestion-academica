# Manejo de Modalidades — Documentación Técnica

> **Reglas de negocio:** `[BR-MOD-01]` – `[BR-MOD-05]`, `[BR-FE-01]` – `[BR-FE-03]`, `[BR-AN-01]`  
> **Última actualización:** 2026-04-05  
> **Estado:** Implementado y con tests

---

## 1. Visión general

CENFOTEC ofrece tres tipos de programa académico, cada uno con su propia estructura temporal:

| Modalidad     | Prefijo   | Periodos / año | Ejemplo                         |
| ------------- | --------- | -------------- | ------------------------------- |
| Cuatrimestral | `C`       | 3              | `C1 2025`, `C2 2025`, `C3 2025` |
| Mensual       | `M`, `MT` | hasta 10       | `M1 2025`, `MT3 2025`           |
| B2B           | `B2B`     | variable       | `B2B-EMPRESA-2025-Q1`           |

Existe una cuarta modalidad técnica, `DESCONOCIDA`, que actúa como fallback para datos legacy o no parseables.

### Principio de aislamiento `[BR-MOD-02]`

> Las evaluaciones de una modalidad **nunca** se mezclan con las de otra en cálculos analíticos ni en la detección de alertas.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CUATRIMESTRAL   │    │    MENSUAL      │    │      B2B        │
│  C1, C2, C3      │    │  M1–M10, MT1–10 │    │  B2B-*          │
│  ────────────    │    │  ────────────   │    │  ────────────   │
│  analytics       │    │  analytics      │    │  analytics      │
│  alerts          │    │  alerts         │    │  alerts         │
│  dashboards      │    │  dashboards     │    │  dashboards     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                     ▲                      ▲
         └─────────────────────┴──────────────────────┘
                     NO cross-modalidad queries
```

---

## 2. Enum canónico (backend)

**Archivo:** `app/domain/entities/enums.py`

```python
class Modalidad(StrEnum):
    CUATRIMESTRAL = "CUATRIMESTRAL"
    MENSUAL       = "MENSUAL"
    B2B           = "B2B"
    DESCONOCIDA   = "DESCONOCIDA"
```

`StrEnum` permite comparación directa con strings (`modalidad == "CUATRIMESTRAL"`) y serialización JSON transparente.

---

## 3. Determinación automática de modalidad

**Archivo:** `app/domain/periodo.py` — `determinar_modalidad()`

```python
def determinar_modalidad(periodo: str) -> Modalidad:
    normalizado = normalizar_periodo(periodo)   # upper + trim

    if normalizado.startswith("B2B"):
        return Modalidad.B2B

    if _RE_FULL_CUATRIMESTRAL.match(normalizado):  # ^C[1-3]\s+\d{4}$
        return Modalidad.CUATRIMESTRAL

    if _RE_FULL_MENSUAL.match(normalizado):         # ^(MT?)\d{1,2}\s+\d{4}$
        # Valida rango numérico: M(1-10), MT(1-10)
        ...
        return Modalidad.MENSUAL

    return Modalidad.DESCONOCIDA  # Fallback [BR-MOD-03]
```

### Regexes de clasificación

| Regex                        | Modalidad     | Match                  | No match               |
| ---------------------------- | ------------- | ---------------------- | ---------------------- |
| `^C([1-3])\s+(\d{4})$`       | CUATRIMESTRAL | `C1 2025`, `C3 2024`   | `C4 2025`, `C12 2024`  |
| `^(MT?)(\d{1,2})\s+(\d{4})$` | MENSUAL       | `M1 2025`, `MT10 2024` | `M11 2025`, `MX3 2024` |
| `^B2B[\s-].+`                | B2B           | `B2B-EMPRESA-2025`     | `B2BEMPRESA`           |
| (ninguno)                    | DESCONOCIDA   | `garbage`, `2025-Q1`   | —                      |

### Validación de rangos `[BR-MOD-03]`

| Prefijo | Mínimo | Máximo |
| ------- | ------ | ------ |
| `C`     | 1      | 3      |
| `M`     | 1      | 10     |
| `MT`    | 1      | 10     |

Un `C4 2025` o `M11 2025` produce `DESCONOCIDA` (fuera de rango).

---

## 4. Persistencia

### 4.1 Columnas en `evaluaciones` (`app/domain/entities/evaluacion.py`)

```python
modalidad: Mapped[str] = mapped_column(
    String(20), nullable=False, default="DESCONOCIDA", index=True)
año: Mapped[int] = mapped_column(SmallInteger, nullable=False)
periodo_orden: Mapped[int] = mapped_column(SmallInteger, nullable=False)
```

### 4.2 Constraints

```sql
CHECK (modalidad IN ('CUATRIMESTRAL', 'MENSUAL', 'B2B', 'DESCONOCIDA'))
CHECK (año >= 2020)
CHECK (puntaje_general IS NULL OR (puntaje_general >= 0 AND puntaje_general <= 100))
```

### 4.3 Índices

| Índice                                | Columnas                          | Propósito                                  | Origen                      |
| ------------------------------------- | --------------------------------- | ------------------------------------------ | --------------------------- |
| `ix_evaluaciones_modalidad`           | `modalidad`                       | Filtro simple por modalidad                | `index=True` en columna     |
| `ix_evaluaciones_modalidad_periodo`   | `(modalidad, periodo)`            | Queries analíticas por modalidad + periodo | `__table_args__` del entity |
| `ix_evaluaciones_modalidad_año_orden` | `(modalidad, año, periodo_orden)` | Ordenamiento temporal dentro de modalidad  | `__table_args__` del entity |

> **Nota:** El índice single-column `ix_evaluaciones_modalidad` se genera implícitamente por el `index=True` en la columna mapped. Los dos índices compuestos están declarados explícitamente en `__table_args__`.

### 4.4 Migración 0007

La migración que introdujo modalidad:

1. Agrega las 3 columnas con `server_default` seguro (`DESCONOCIDA`, `2020`, `0`)
2. Crea los 3 índices y el CHECK constraint
3. Los rows existentes reciben `DESCONOCIDA` como backfill
4. Los `server_default` se eliminan al final (la app calcula los valores reales)

---

## 5. Pipeline de ingesta

Cuando se procesa un documento PDF, el parser invoca `determinar_modalidad()` para cada evaluación y almacena el resultado en `PeriodoData`:

```python
class PeriodoData(BaseModel):
    periodo_raw: str
    periodo_normalizado: str
    modalidad: Literal["CUATRIMESTRAL", "MENSUAL", "B2B", "DESCONOCIDA"]
    año: int
    periodo_orden: int
    prefijo: str
    numero: int
```

Flujo:

```
PDF → Parser extrae "C2 2025"
    → normalizar_periodo("C2 2025") → "C2 2025"
    → determinar_modalidad("C2 2025") → CUATRIMESTRAL
    → parse_periodo("C2 2025") → PeriodoInfo(...)
    → PeriodoData(modalidad="CUATRIMESTRAL", año=2025, periodo_orden=2, ...)
    → INSERT INTO evaluaciones (modalidad='CUATRIMESTRAL', año=2025, ...)
```

---

## 6. Aislamiento en alertas `[BR-MOD-05]`

### 6.1 Modalidades alertables

```python
_ALERTABLE_MODALIDADES: list[str] = [
    Modalidad.CUATRIMESTRAL.value,
    Modalidad.MENSUAL.value,
    Modalidad.B2B.value,
]
# DESCONOCIDA queda EXCLUIDA — no genera alertas
```

### 6.2 Ejecución por modalidad

```python
class AlertEngine:
    async def run_all(self) -> AlertRunResult:
        for modalidad in _ALERTABLE_MODALIDADES:
            partial = await self.run_for_modalidad(modalidad)
            # Acumula resultados...

    async def run_for_modalidad(self, modalidad: str) -> AlertRunResult:
        # 1. Obtener últimos 2 periodos DE ESTA modalidad
        periodos = await self._repo.find_last_two_periods(modalidad)

        # 2. Cargar snapshots filtrados por modalidad
        snapshots = await self._repo.load_snapshots(modalidad, periodos)

        # 3. Detectores corren sobre datos de UNA sola modalidad
        for detector in self._detectors:
            candidates = detector.detect(snapshots, periodos)
```

### 6.3 Queries filtradas por modalidad

```sql
-- find_last_two_periods (alerta_repo.py)
SELECT DISTINCT periodo, año, periodo_orden
FROM evaluaciones
WHERE modalidad = :modalidad
ORDER BY año DESC, periodo_orden DESC
LIMIT 2

-- load_snapshots (alerta_repo.py)
SELECT docente_nombre, periodo, AVG(puntaje_general) ...
FROM evaluaciones
WHERE modalidad = :modalidad AND periodo IN (:periodos)
GROUP BY docente_nombre, periodo
```

---

## 7. Tipos frontend

### 7.1 Tipos base (`src/types/index.ts`)

```typescript
type Modalidad = "CUATRIMESTRAL" | "MENSUAL" | "B2B";
type ModalidadConDesconocida = Modalidad | "DESCONOCIDA";
```

**Regla:** La UI solo ofrece `Modalidad` (3 opciones) para selección. `ModalidadConDesconocida` se usa internamente para manejar datos legacy.

### 7.2 En interfaces tipadas

```typescript
interface AlertaResponse {
  modalidad: Modalidad; // Siempre una de las 3 — DESCONOCIDA no genera alertas
  // ...
}

interface AlertFilters {
  modalidad?: string; // Query param opcional
  // ...
}
```

---

## 8. Utilidades frontend (`src/lib/business-rules.ts`)

### 8.1 Constante MODALIDADES `[BR-FE-02]`

```typescript
interface ModalidadOption {
  value: Modalidad;
  label: string;
  description: string;
}

const MODALIDADES: readonly ModalidadOption[] = [
  {
    value: "CUATRIMESTRAL",
    label: "Cuatrimestral",
    description: "C1–C3 (3 periodos por año)",
  },
  { value: "MENSUAL", label: "Mensual", description: "M1–M10, MT1–MT10" },
  { value: "B2B", label: "B2B", description: "Programas corporativos" },
];
```

### 8.2 Funciones

| Función                  | Firma                                   | Descripción                               |
| ------------------------ | --------------------------------------- | ----------------------------------------- |
| `modalidadLabel()`       | `(m: ModalidadConDesconocida) → string` | Label amigable — incluye `"Desconocida"`  |
| `isModalidad()`          | `(v: string) → v is Modalidad`          | Type guard — excluye `DESCONOCIDA`        |
| `isValidPeriodo()`       | `(p: string) → boolean`                 | Valida formato de periodo contra regexes  |
| `modalidadFromPeriodo()` | `(p: string) → ModalidadConDesconocida` | Infiere modalidad desde string de periodo |

### 8.3 Regexes frontend (espejo del backend)

```typescript
const RE_CUATRIMESTRAL = /^C[1-3]\s+\d{4}$/i;
const RE_MENSUAL = /^MT?\d{1,2}\s+\d{4}$/i;
const RE_B2B = /^B2B[\s-].+/i;
```

---

## 9. Componente ModalidadSelector

**Archivo:** `src/components/dashboard/command-center.tsx`

Componente local que renderiza un grupo de botones tipo "tab" para filtrar por modalidad:

```
┌──────────────────────────────────────────────────────────┐
│  🔍  [ Todas ]  [ Cuatrimestral ]  [ Mensual ]  [ B2B ] │
└──────────────────────────────────────────────────────────┘
```

### Comportamiento

| Acción                | Efecto                                                          |
| --------------------- | --------------------------------------------------------------- |
| Click "Todas"         | `setModalidad(null)` → fetch sin filtro                         |
| Click "Cuatrimestral" | `setModalidad("CUATRIMESTRAL")` → fetch filtrado                |
| Cambio de filtro      | `useEffect` en `useCommandCenter` dispara `fetchAll(modalidad)` |

### Cascada de filtrado `[BR-FE-03]`

```
ModalidadSelector → setModalidad(mod)
    → useEffect([modalidad]) dispara fetchAll(mod)
        → AbortController cancela request anterior
        → Promise.all([dashboard, alertSummary, alerts(mod)])
        → Re-render con datos filtrados
```

El cambio de modalidad **cancela** cualquier request en vuelo (mediante `AbortController`) y lanza un fetch completo nuevo.

---

## 10. Manejo de DESCONOCIDA

### 10.1 Backend

| Contexto                 | Comportamiento                                        |
| ------------------------ | ----------------------------------------------------- |
| `determinar_modalidad()` | Retorna `DESCONOCIDA` cuando ningún regex matchea     |
| `validar_periodo()`      | **Lanza `ValidationError`** si se pasa `DESCONOCIDA`  |
| Motor de alertas         | **Excluye** `DESCONOCIDA` de `_ALERTABLE_MODALIDADES` |
| Entity default           | Column default es `"DESCONOCIDA"` (backfill seguro)   |
| CHECK constraint         | Permite el valor `"DESCONOCIDA"` a nivel de DB        |

### 10.2 Frontend

| Contexto                        | Comportamiento                                                              |
| ------------------------------- | --------------------------------------------------------------------------- |
| `ModalidadSelector`             | **No muestra** opción `DESCONOCIDA` (itera `MODALIDADES`, que solo tiene 3) |
| `modalidadLabel("DESCONOCIDA")` | Retorna `"Desconocida"` — para display informativo si aparece               |
| `isModalidad("DESCONOCIDA")`    | Retorna `false` — no es una modalidad seleccionable                         |
| `type Modalidad`                | No incluye `"DESCONOCIDA"`                                                  |
| `type ModalidadConDesconocida`  | Incluye `"DESCONOCIDA"` — solo para manejo interno                          |

---

## 11. Impacto en backend: reglas para desarrollo

### 11.1 Nuevas queries analíticas

Toda query que calcule promedios, tendencias o KPIs **DEBE** filtrar por modalidad:

```python
# ✅ Correcto — aislamiento respetado
stmt = select(func.avg(Evaluacion.puntaje_general)) \
    .where(Evaluacion.modalidad == modalidad)

# ❌ Incorrecto — mezcla todas las modalidades
stmt = select(func.avg(Evaluacion.puntaje_general))
```

### 11.2 Nuevos detectores de alertas

Todo nuevo detector recibe snapshots ya filtrados por modalidad (el engine se encarga):

```python
class NuevoDetector:
    def detect(
        self,
        snapshots: dict[str, list[DocenteCursoSnapshot]],
        periodos: list[str],
    ) -> list[AlertCandidate]:
        # snapshots ya son de UNA sola modalidad
        ...
```

### 11.3 Cache keys

Si se implementa cache para un endpoint que depende de modalidad, la clave **DEBE** incluir la modalidad:

```python
# ✅ Correcto
key = f"analytics:evolucion:{modalidad}:{periodo}"

# ❌ Incorrecto — cache compartida entre modalidades
key = f"analytics:evolucion:{periodo}"
```

---

## 12. Impacto en frontend: reglas para desarrollo

### 12.1 Agregar nueva modalidad `[BR-EXT-01]`

Para agregar una modalidad (ej. `INTENSIVO`):

1. **Backend:** Agregar valor al enum `Modalidad` + regex en `periodo.py` + migración ALTER CHECK
2. **Frontend:** Agregar a `type Modalidad` + agregar entrada a `MODALIDADES` + agregar label a `MODALIDAD_LABELS`
3. **Automático:** `ModalidadSelector` renderiza la nueva opción sin cambios

### 12.2 Type guards

Siempre usar `isModalidad()` antes de aceptar input del usuario como `Modalidad`:

```typescript
// ✅ Correcto
const raw = searchParams.get("modalidad");
if (raw && isModalidad(raw)) {
  setModalidad(raw); // TypeScript sabe que es Modalidad
}

// ❌ Incorrecto — cast directo
setModalidad(searchParams.get("modalidad") as Modalidad);
```

---

## 13. Tests

### 13.1 Backend (`tests/unit/test_periodo.py`)

| Test                                       | Cobertura                  |
| ------------------------------------------ | -------------------------- |
| `test_determinar_modalidad_cuatrimestral`  | C1–C3 → CUATRIMESTRAL      |
| `test_determinar_modalidad_mensual`        | M1–M10, MT1–MT10 → MENSUAL |
| `test_determinar_modalidad_b2b`            | B2B-\* → B2B               |
| `test_determinar_modalidad_desconocida`    | "garbage" → DESCONOCIDA    |
| `test_determinar_modalidad_fuera_de_rango` | C4, M11 → DESCONOCIDA      |

### 13.2 Frontend (`tests/unit/business-rules.test.ts`)

| Test                   | Cobertura                                                         |
| ---------------------- | ----------------------------------------------------------------- |
| `isModalidad`          | Acepta las 3 válidas, rechaza `DESCONOCIDA` y strings arbitrarios |
| `modalidadLabel`       | Labels correctos para las 4 (incluida DESCONOCIDA)                |
| `modalidadFromPeriodo` | Parsea periodos → modalidad correcta, fallback DESCONOCIDA        |
| `isValidPeriodo`       | Valida formatos conocidos, rechaza malformados                    |
| `MODALIDADES`          | Exactamente 3 opciones, orden correcto                            |

---

## 14. Ejemplos de validación

### ✅ Ingesta correcta

```
Input:  periodo_raw = "c2 2025"
Normalizado:  "C2 2025"
Modalidad:    CUATRIMESTRAL
año:          2025
periodo_orden: 2
→ INSERT OK, CHECK constraint satisfied
```

### ✅ Filtrado correcto de alertas

```
run_all() itera: [CUATRIMESTRAL, MENSUAL, B2B]
→ DESCONOCIDA no se procesa
→ Cada run_for_modalidad() solo ve datos de su modalidad
→ No hay contaminación cross-modalidad
```

### ✅ Selector frontend correcto

```
ModalidadSelector renderiza: [Todas, Cuatrimestral, Mensual, B2B]
→ "Desconocida" NO aparece como opción
→ Click en "Mensual" → setModalidad("MENSUAL")
→ fetchAll("MENSUAL") → API con ?modalidad=MENSUAL
```

### ❌ Query sin aislamiento

```python
stmt = select(func.avg(Evaluacion.puntaje_general)) \
    .where(Evaluacion.periodo == "C2 2025")
# ERROR: incluye evaluaciones B2B que casualmente tienen
# "C2 2025" en algún campo (violación [BR-MOD-02])
```

### ❌ Cast inseguro en frontend

```typescript
const m = "INVALID_VALUE" as Modalidad;
// ERROR: TypeScript lo permite pero runtime fallará al
// buscar en MODALIDAD_LABELS → retorna undefined
```

### ❌ Cache sin modalidad

```python
key = f"analytics:{periodo}"
# ERROR: La primera modalidad que cachea "C2 2025" contamina
# el resultado de las demás modalidades (violación [BR-MOD-02])
```
