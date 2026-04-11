# Estrategia de Testing

> Pirámide de tests, herramientas, fixtures y convenciones.
> Última actualización: 2026-04-08

---

## Pirámide de Tests

```
         ┌─────────┐
         │  E2E    │  Playwright (navegador real)
         │  (pocos)│
        ┌┴─────────┴┐
        │ API Tests  │  httpx + AsyncClient (FastAPI TestClient)
        │ (moderados)│
       ┌┴────────────┴┐
       │ Integration   │  pytest-asyncio + testcontainers (PostgreSQL)
       │ (moderados)   │
      ┌┴───────────────┴┐
      │   Unit Tests     │  pytest / Vitest (rápidos, sin I/O)
      │   (muchos)       │
      └──────────────────┘
```

---

## Backend (Python)

### Stack de Testing

| Herramienta        | Propósito                                            |
| ------------------ | ---------------------------------------------------- |
| **pytest**         | Framework de tests                                   |
| **pytest-asyncio** | Soporte para tests async                             |
| **testcontainers** | PostgreSQL real en contenedor para integration tests |
| **httpx**          | Cliente HTTP async para tests de API                 |
| **ruff**           | Linting (reemplaza flake8 + isort)                   |

### Capas de Tests

#### Unit Tests (`tests/unit/`) — 26 archivos

Tests de funciones puras sin I/O ni base de datos:

- **Parser:** `test_parser.py`, `test_header_extractor.py`, `test_metrics_extractor.py`, `test_courses_extractor.py`, `test_comments_extractor.py`, `test_parser_periodo.py`, `test_parser_schemas.py`, `test_parse_result.py`
- **Clasificador:** `test_classifier.py` — temas, sentimiento, edge cases
- **Alertas:** `test_alert_engine.py`, `test_alert_engine_edge_cases.py`, `test_alert_rules.py` — motor de reglas de negocio
- **Query:** `test_query_service.py`, `test_prompt_templates.py` — pipeline RAG
- **Reglas de negocio:** `test_business_rules.py` — 150+ reglas BR-\*
- **Schemas:** `test_schemas.py`, `test_qualitative_schemas.py`
- **Infraestructura:** `test_cache.py`, `test_rate_limiter.py`, `test_gemini_exceptions.py`, `test_gemini_retry.py`
- **Config:** `test_config_routes.py` — endpoint de umbrales de alerta
- **Dominio:** `test_invariants.py` — invariantes de dominio
- **Otros:** `test_exceptions.py`, `test_factories.py`, `test_periodo.py`

```bash
pytest tests/unit/ -v
```

#### Integration Tests (`tests/integration/`) — 7 archivos

Tests con base de datos PostgreSQL real (via testcontainers) para verificar repositorios:

- `test_documento_repo.py` — CRUD de documentos
- `test_evaluacion_repo.py` — CRUD de evaluaciones con relaciones
- `test_analytics_repo.py` — Queries de dimensiones y cursos
- `test_qualitative_repo.py` — Queries de comentarios y clasificación
- `test_processing_service.py` — Pipeline de procesamiento end-to-end
- `test_query_service.py` — Pipeline RAG con fake Gemini
- `test_alerta_repo.py` — CRUD y filtros de alertas

```bash
pytest tests/integration/ -v
```

#### API Tests (`tests/api/`) — 11 archivos

Tests HTTP contra la API completa con dependencias mockeadas:

- `test_documentos.py` — Upload, listado, periodos, eliminación
- `test_evaluaciones.py` — Listado con filtros (modalidad, periodo, docente)
- `test_analytics.py` — 5 endpoints de métricas
- `test_qualitative.py` — 7 endpoints de comentarios
- `test_upload.py` — Flujo de carga de archivos
- `test_health.py` — Health check endpoint
- `test_query.py` — Consultas IA con fake Gemini
- `test_security.py` — Headers de seguridad, trusted proxy, rate limiter fallback
- `test_modalidad_isolation.py` — 14 tests de aislamiento por modalidad [BR-MOD-02]
- `test_modalidad_enforcement.py` — Enforcement de modalidad requerida en endpoints
- `test_alertas.py` — CRUD alertas, summary, rebuild

```bash
pytest tests/api/ -v
```

### Fixtures Compartidas

#### Base de Datos (`conftest.py`)

Los tests de API e integración usan una base de datos PostgreSQL real a través de testcontainers. Cada test ejecuta dentro de una transacción que se revierte al finalizar, garantizando aislamiento total.

```python
# conftest.py usa testcontainers para PostgreSQL real
# Esto garantiza compatibilidad total con asyncpg + funciones PostgreSQL
```

#### Fakes (`tests/fixtures/fakes.py`)

| Fake                | Reemplaza  | Comportamiento                                                     |
| ------------------- | ---------- | ------------------------------------------------------------------ |
| `FakeFileStorage`   | MinIO/S3   | Dict in-memory, `upload()` guarda bytes, `download()` los recupera |
| `FakeGeminiGateway` | Gemini API | Retorna respuestas enlatadas sin llamar a la API real              |

#### Factories (`tests/fixtures/factories.py`)

Funciones para crear entidades de dominio con valores por defecto razonables:

```python
create_documento(nombre="test.pdf", estado="subido", ...)
create_evaluacion(docente_nombre="Juan", periodo="I-2025", ...)
```

#### ASGI Test Client

```python
@pytest.fixture
async def client(db, fake_storage, fake_gemini):
    # Override all external dependencies
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_file_storage] = lambda: fake_storage
    app.dependency_overrides[get_gemini_gateway] = lambda: fake_gemini
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

### Ejecución

```bash
# Todos los tests
cd backend && pytest tests/ -v

# Con cobertura
pytest tests/ --cov=app --cov-report=html

# Filtrar por marca o nombre
pytest tests/ -k "test_classifier"
pytest tests/unit/ -v
```

---

## Frontend (TypeScript)

### Stack de Testing

| Herramienta                   | Propósito                                                   |
| ----------------------------- | ----------------------------------------------------------- |
| **Vitest 4.1.2**              | Framework de tests (alternativa a Jest, integrado con Vite) |
| **@testing-library/react 16** | Renderizado y queries de componentes                        |
| **jsdom**                     | DOM virtual para tests unitarios                            |
| **Playwright**                | Tests E2E con navegador real (Chromium)                     |

### Configuración de Vitest

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globals: true, // describe, it, expect globales
    environment: "jsdom", // DOM virtual
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}", "src/**/*.test.{ts,tsx}"],
    exclude: ["node_modules", ".next", "e2e"],
    css: false, // No procesa CSS en tests
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/index.ts", "src/types/**", "src/components/ui/**"],
    },
  },
});
```

### Capas de Tests

#### Unit Tests (`tests/unit/`)

Tests de hooks, utilidades y lógica de negocio:

```bash
cd frontend && npx vitest run tests/unit/
```

#### Component Tests (`tests/components/`)

Tests de componentes React con `@testing-library/react`:

```bash
cd frontend && npx vitest run tests/components/
```

#### E2E Tests (`e2e/`)

Tests de navegación y flujos completos con Playwright:

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: "./e2e",
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `npx next dev -p ${PORT}`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
  },
});
```

```bash
cd frontend && npx playwright test
```

### Ejecución

```bash
# Todos los tests unitarios y de componentes
cd frontend && npm test

# Con interfaz visual
npm run test:ui

# Con cobertura
npm run test:coverage

# E2E
npm run test:e2e
```

---

## Comandos Unificados (Make)

```bash
make test         # Backend + frontend (unitarios)
make test-back    # Solo backend (pytest)
make test-front   # Solo frontend (vitest)
make test-e2e     # E2E con Playwright
make lint         # Ruff (backend) + ESLint (frontend)
```

---

## Convenciones

| Convención           | Detalle                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| Nomenclatura         | `test_<funcionalidad>.py` (backend), `<componente>.test.tsx` (frontend) |
| Aislamiento          | Cada test es independiente — no hay orden ni estado compartido          |
| Rollback automático  | Tests backend con transacción que se revierte al finalizar              |
| Fakes sobre mocks    | Preferimos fakes (implementaciones alternativas) sobre `unittest.mock`  |
| Sin I/O en unitarios | Tests unitarios no tocan red, disco ni base de datos                    |
| Setup mínimo         | Los tests crean solo los datos que necesitan                            |

---

## CI/CD

Los tests se ejecutan en CI con GitHub Actions:

```
Backend:  pytest tests/ --cov=app
Frontend: npm test -- --reporter=json
E2E:      npx playwright test (solo en merges a main)
```

Criterios de aprobación:

- 0 tests fallando
- Cobertura backend ≥ 80%
- Cobertura frontend ≥ 70%
