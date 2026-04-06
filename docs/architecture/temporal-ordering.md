# Ordenamiento Cronológico — Documentación Técnica

> **Reglas de negocio:** `[BR-AN-40]` – `[BR-AN-42]`, `[VZ-20]` – `[VZ-21]`  
> **Última actualización:** 2026-04-05  
> **Estado:** Implementado y con tests

---

## 1. Problema

Los periodos académicos se almacenan como strings (`"C2 2025"`, `"M10 2024"`). Un `ORDER BY periodo` lexicográfico produce:

```
❌  C1 2024, C1 2025, C2 2024, C2 2025, C3 2024
✅  C1 2024, C2 2024, C3 2024, C1 2025, C2 2025
```

Para mensual es peor — `M10` ordena antes que `M2` lexicográficamente.

---

## 2. Regla canónica `[BR-AN-40]`

Todos los datos temporales se ordenan por:

1. **Año** (ascendente)
2. **Prefijo** (ascendente: `B2B` < `C` < `M` < `MT`)
3. **Número de periodo** (ascendente)

### Secuencias correctas

**Cuatrimestral:**

```
C1 2024 → C2 2024 → C3 2024 → C1 2025 → C2 2025 → C3 2025
```

**Mensual:**

```
M1 2025 → M2 2025 → … → M10 2025 → M1 2026
MT1 2025 → MT2 2025 → … → MT10 2025 → MT1 2026
```

**Continuidad inter-año `[BR-AN-42]`:**

```
… C3 2024 → C1 2025 → C2 2025 …
```

---

## 3. Diseño de la solución

### Estrategia: ordenar en Python/TypeScript, no en SQL

**¿Por qué no una columna computada o `ORDER BY` SQL?**

El formato de periodo es un string libre (`"C2 2025"`, `"M10 2024"`, `"B2B-EMPRESA-2025"`). Parsear este formato requiere lógica regex que ya existe en `periodo.py`. Duplicar esa lógica en un `GENERATED COLUMN` o función SQL:

- Duplicaría la lógica de dominio
- Requeriría migración adicional
- Dificultaría el testing

**Solución elegida:** Fetch sin ORDER BY → sort en Python usando `sort_periodos()`.

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│   SQL    │────▶│  Fetch   │────▶│ sort_periodos │────▶│ Response │
│ GROUP BY │     │ unsorted │     │  (Python)     │     │ ordered  │
└──────────┘     └──────────┘     └──────────────┘     └──────────┘
```

El frontend aplica un **re-sort defensivo** adicional para garantizar orden incluso si el backend fallara.

---

## 4. Implementación backend

### 4.1 Función de sort key (`app/domain/periodo.py`)

```python
@dataclass(frozen=True)
class PeriodoInfo:
    periodo_normalizado: str   # "C2 2025"
    modalidad: Modalidad       # CUATRIMESTRAL
    año: int                   # 2025
    periodo_orden: int         # 2  (derivado de número)
    prefijo: str               # "C"
    numero: int                # 2

def periodo_sort_key(info: PeriodoInfo) -> tuple[int, str, int]:
    """(año, prefijo, numero) — el sort key canónico [BR-AN-40]."""
    return (info.año, info.prefijo, info.numero)
```

### 4.2 Sort de diccionarios (`app/domain/periodo.py`)

```python
def _periodo_str_sort_key(periodo_str: str) -> tuple[int, str, int]:
    """Parsea una string de periodo → sort key. Imparseable → (9999, str, 0)."""
    try:
        info = parse_periodo(periodo_str)
        return periodo_sort_key(info)
    except (ValidationError, Exception):
        return (9999, periodo_str, 0)

def sort_periodos(rows: list[dict], *, key: str = "periodo") -> list[dict]:
    """Ordena cronológicamente [BR-AN-40]. Imparseable va al final."""
    return sorted(rows, key=lambda r: _periodo_str_sort_key(r[key]))
```

### 4.3 Puntos de uso

| Archivo                | Método                 | Antes                           | Después                   |
| ---------------------- | ---------------------- | ------------------------------- | ------------------------- |
| `analytics_repo.py`    | `evolucion_periodos()` | `.order_by(Evaluacion.periodo)` | `sort_periodos(unsorted)` |
| `dashboard_service.py` | `_tendencia()`         | `.order_by(Evaluacion.periodo)` | `sort_periodos(unsorted)` |

**Patrón estándar:**

```python
from app.domain.periodo import sort_periodos

rows = (await self.session.execute(stmt)).all()
unsorted = [
    {"periodo": r.periodo, "promedio": round(float(r.promedio), 2), ...}
    for r in rows
]
return sort_periodos(unsorted)
```

### 4.4 Regexes de parsing

| Modalidad     | Regex                        | Ejemplos                          |
| ------------- | ---------------------------- | --------------------------------- |
| Cuatrimestral | `^C([1-3])\s+(\d{4})$`       | `C1 2025`, `C3 2024`              |
| Mensual       | `^(MT?)(\d{1,2})\s+(\d{4})$` | `M1 2026`, `M10 2025`, `MT3 2024` |
| B2B           | `^B2B[\s-].+`                | `B2B-EMPRESA-2025-Q1`             |

---

## 5. Implementación frontend

### 5.1 Utilidades (`src/lib/periodo-sort.ts`)

```typescript
interface PeriodoSortKey {
  año: number; // 2025
  prefijo: string; // "C"
  numero: number; // 2
}

// Parsea "C2 2025" → { año: 2025, prefijo: "C", numero: 2 }
// Imparseable → { año: 9999, prefijo: "ZZZ", numero: 0 }
function parsePeriodoKey(periodo: string): PeriodoSortKey;

// Comparador para Array.sort()
function comparePeriodos(a: string, b: string): number;

// Ordena array de objetos por campo periodo
function sortByPeriodo<T>(items: T[], key?: keyof T): T[];
```

### 5.2 Puntos de uso

| Archivo                   | Contexto           | Uso                                                   |
| ------------------------- | ------------------ | ----------------------------------------------------- |
| `use-analytics.ts`        | `fetchAll()`       | `sortByPeriodo(evolucion)` tras el fetch              |
| `use-command-center.ts`   | `fetchAll()`       | `sortByPeriodo(dashboard.tendencia)` tras Promise.all |
| `analytics-dashboard.tsx` | `useMemo` periodos | `.sort(comparePeriodos)` para el dropdown de filtros  |

### 5.3 Re-exports desde `business-rules.ts`

```typescript
// Los consumidores pueden importar desde un solo punto:
import { comparePeriodos, sortByPeriodo } from "@/lib/business-rules";
```

---

## 6. Impacto en frontend

### 6.1 Gráficos de tendencia `[VZ-20]`

Todos los gráficos con eje temporal (Recharts `<AreaChart>`, `<LineChart>`) renderizan datos que ya llegan ordenados por el hook. El componente **no** hace sort adicional — confía en el array order.

```
Hook (sortByPeriodo) → State → Chart (renders in array order)
```

### 6.2 Filtros de periodo `[VZ-21]`

El dropdown de periodos usa `comparePeriodos` para mostrar opciones en orden cronológico:

```typescript
const periodos = useMemo(
  () => [...new Set(evolucion.map((e) => e.periodo))].sort(comparePeriodos),
  [evolucion],
);
```

### 6.3 Labels de eje X `[VZ-21]`

Los labels del eje X son las strings originales (`"C1 2025"`, `"M3 2026"`), legibles directamente.

---

## 7. Impacto en backend

### 7.1 Regla para nuevas queries

Toda query que retorne datos temporales **MUST** usar `sort_periodos()`:

```python
# ✅ Correcto
unsorted = [{"periodo": r.periodo, ...} for r in rows]
return sort_periodos(unsorted)

# ❌ Incorrecto — lexicográfico
stmt = stmt.order_by(Evaluacion.periodo)
```

### 7.2 Cache

Las claves de cache no cambian — el sort ocurre antes de devolver, no afecta la estructura del resultado.

### 7.3 Alertas

El motor de alertas usa `find_last_two_periods()` que ya ordena por `(año DESC, periodo_orden DESC)` a nivel SQL porque las columnas `año` y `periodo_orden` son numéricas en la tabla.

---

## 8. Manejo de periodos imparseable

| Capa                         | Comportamiento                                                      |
| ---------------------------- | ------------------------------------------------------------------- |
| Backend `sort_periodos()`    | Retorna `(9999, raw_string, 0)` → queda al final                    |
| Frontend `parsePeriodoKey()` | Retorna `{ año: 9999, prefijo: "ZZZ", numero: 0 }` → queda al final |
| Ambos                        | No lanzan excepciones — degradación elegante                        |

---

## 9. Tests

### 9.1 Backend (`tests/unit/test_periodo.py`)

| Clase                   | Tests | Cobertura                                                                                                       |
| ----------------------- | ----- | --------------------------------------------------------------------------------------------------------------- |
| `TestPeriodoStrSortKey` | 5     | Cuatrimestral, mensual, MT, imparseable, vacío                                                                  |
| `TestSortPeriodos`      | 10    | Intra-año, cross-year, mensual, MT, vacío, single, imparseable al final, key custom, no-mutate, preserva campos |

### 9.2 Frontend (`tests/unit/periodo-sort.test.ts`)

| Describe          | Tests | Cobertura                                                                                           |
| ----------------- | ----- | --------------------------------------------------------------------------------------------------- |
| `parsePeriodoKey` | 7     | C, M, MT, B2B, case-insensitive, imparseable, vacío                                                 |
| `comparePeriodos` | 6     | Año, prefijo, número, idéntico, cross-year, imparseable                                             |
| `sortByPeriodo`   | 8     | Intra-año, cross-year, mensual, vacío, no-mutate, imparseable al final, key custom, preserva campos |

---

## 10. Ejemplos de validación

### ✅ Orden correcto — cuatrimestral cross-year

```
Input:  [C1 2025, C3 2024, C2 2025, C1 2024]
Output: [C1 2024, C3 2024, C1 2025, C2 2025]
```

### ✅ Orden correcto — mensual numérico

```
Input:  [M10 2024, M1 2024, M5 2024]
Output: [M1 2024, M5 2024, M10 2024]
```

### ✅ Imparseable al final

```
Input:  ["garbage", "C1 2024", "C2 2024"]
Output: ["C1 2024", "C2 2024", "garbage"]
```

### ❌ Orden incorrecto — lexicográfico

```
Input:  [C1 2024, C2 2024, C3 2024, C1 2025]
BAD:    [C1 2024, C1 2025, C2 2024, C3 2024]  ← ORDER BY periodo
ERROR:  Violación de [BR-AN-40] — C1 2025 no va antes de C2 2024
```

### ❌ Orden incorrecto — mensual string

```
Input:  [M1 2025, M10 2025, M2 2025]
BAD:    [M1 2025, M10 2025, M2 2025]  ← "M10" < "M2" lexicográficamente
ERROR:  Violación de [BR-AN-40] — M10 va después de M9
```
