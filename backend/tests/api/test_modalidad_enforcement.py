"""BR-MOD-02 enforcement tests — modalidad validation on analytical endpoints.

Analytics endpoints accept **optional** modalidad (missing → returns all data).
Qualitative and alertas endpoints still **require** modalidad.
All endpoints reject **invalid** modalidad values (e.g. DESCONOCIDA).

Dropdown-population endpoints (/periodos, /escuelas, /cursos, /filtros)
are explicitly verified to still work WITHOUT modalidad.
"""

import pytest

# ---------------------------------------------------------------------------
# Analytical endpoints — modalidad is OPTIONAL (missing → all data)
# ---------------------------------------------------------------------------

_ANALYTICS_ENDPOINTS = [
    "/api/v1/analytics/resumen",
    "/api/v1/analytics/docentes",
    "/api/v1/analytics/dimensiones",
    "/api/v1/analytics/evolucion",
    "/api/v1/analytics/ranking",
]

# ---------------------------------------------------------------------------
# Endpoints that still REQUIRE modalidad
# ---------------------------------------------------------------------------

_QUALITATIVE_ENDPOINTS = [
    "/api/v1/qualitative/resumen",
    "/api/v1/qualitative/comentarios",
    "/api/v1/qualitative/distribucion/temas",
    "/api/v1/qualitative/distribucion/sentimiento",
    "/api/v1/qualitative/nube-palabras",
]

_ALERTA_ENDPOINTS = [
    "/api/v1/alertas",
    "/api/v1/alertas/summary",
]

_ALL_MANDATORY = _QUALITATIVE_ENDPOINTS + _ALERTA_ENDPOINTS
_ALL_VALIDATED = _ANALYTICS_ENDPOINTS + _QUALITATIVE_ENDPOINTS + _ALERTA_ENDPOINTS


# ── Analytics: missing modalidad → 200 (returns all data) ────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", _ANALYTICS_ENDPOINTS)
async def test_analytics_without_modalidad_returns_200(client, endpoint):
    """Analytics endpoints work without modalidad (returns all data)."""
    resp = await client.get(endpoint)
    assert resp.status_code == 200, f"{endpoint} should return 200 without modalidad"


# ── Mandatory endpoints: missing modalidad → 422 ─────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", _ALL_MANDATORY)
async def test_missing_modalidad_returns_422(client, endpoint):
    """Endpoints that require modalidad must reject requests without it."""
    resp = await client.get(endpoint)
    assert resp.status_code == 422, f"{endpoint} should return 422 without modalidad"


# ── Invalid modalidad → 422 (all endpoints) ─────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", _ALL_VALIDATED)
async def test_invalid_modalidad_returns_422(client, endpoint):
    """Invalid modalidad values must be rejected."""
    resp = await client.get(endpoint, params={"modalidad": "DESCONOCIDA"})
    assert resp.status_code == 422, f"{endpoint} should reject DESCONOCIDA"


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", _ALL_VALIDATED)
async def test_random_modalidad_returns_422(client, endpoint):
    """Random strings as modalidad must be rejected."""
    resp = await client.get(endpoint, params={"modalidad": "FOO_BAR"})
    assert resp.status_code == 422, f"{endpoint} should reject arbitrary strings"


# ── Valid modalidad → 200 (all endpoints) ────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", _ALL_VALIDATED)
async def test_valid_modalidad_returns_200(client, endpoint):
    """Endpoints must accept valid modalidad values (empty DB → 200)."""
    resp = await client.get(endpoint, params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200, f"{endpoint} should accept CUATRIMESTRAL"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "modalidad", ["CUATRIMESTRAL", "MENSUAL", "B2B", "cuatrimestral", "Mensual"]
)
async def test_resumen_accepts_valid_modalidad_variants(client, modalidad):
    """Case-insensitive valid modalidad values must be accepted."""
    resp = await client.get("/api/v1/analytics/resumen", params={"modalidad": modalidad})
    assert resp.status_code == 200


# ── Dropdown endpoints still work without modalidad ─────────────────────


_DROPDOWN_ENDPOINTS = [
    "/api/v1/analytics/periodos",
    "/api/v1/analytics/escuelas",
    "/api/v1/analytics/cursos",
    "/api/v1/qualitative/filtros",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", _DROPDOWN_ENDPOINTS)
async def test_dropdown_endpoints_work_without_modalidad(client, endpoint):
    """Dropdown-population endpoints must NOT require modalidad."""
    resp = await client.get(endpoint)
    assert resp.status_code == 200, f"{endpoint} should work without modalidad"


# ── Query endpoint (POST) ──────────────────────────────────────────────
# Modalidad is fully optional for the query endpoint — Gemini accesses
# all data by default, so no enforcement tests are needed here.
