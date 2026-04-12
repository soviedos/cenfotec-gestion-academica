"""Integration tests — AlertaRepository against a real PostgreSQL database.

Exercises ``find_last_two_periods``, ``load_snapshots``, and ``upsert_batch``
with real SQL against the testcontainers-managed database.
"""

from __future__ import annotations

import uuid

import pytest

from app.domain.alert_rules import AlertCandidate
from app.domain.entities.enums import Severidad, TipoAlerta
from app.infrastructure.repositories.alerta_repo import AlertaRepository
from app.infrastructure.repositories.documento import DocumentoRepository
from app.infrastructure.repositories.evaluacion import EvaluacionRepository
from tests.fixtures.factories import make_comentario, make_documento, make_evaluacion

pytestmark = pytest.mark.integration

# ── Helpers ──────────────────────────────────────────────────────────────


def _eval(
    doc_id,
    *,
    docente="Prof. García",
    periodo="C1 2025",
    modalidad="CUATRIMESTRAL",
    año=2025,
    orden=1,
    puntaje=85.0,
    materia="ISW-101 Prog I",
):
    return make_evaluacion(
        documento_id=doc_id,
        docente_nombre=docente,
        periodo=periodo,
        modalidad=modalidad,
        año=año,
        periodo_orden=orden,
        materia=materia,
        puntaje_general=puntaje,
        estado="completado",
    )


def _candidate(
    *,
    docente="Prof. García",
    curso="ISW-101 Prog I",
    periodo="C1 2025",
    tipo=TipoAlerta.BAJO_DESEMPENO,
    eval_id=None,
):
    return AlertCandidate(
        evaluacion_id=eval_id or uuid.uuid4(),
        docente_nombre=docente,
        curso=curso,
        periodo=periodo,
        modalidad="CUATRIMESTRAL",
        tipo_alerta=tipo,
        metrica_afectada="puntaje_general",
        valor_actual=55.0,
        valor_anterior=None,
        descripcion="Test alert",
        severidad=Severidad.ALTA,
    )


# ═══════════════════════════════════════════════════════════════════════
# find_last_two_periods
# ═══════════════════════════════════════════════════════════════════════


class TestFindLastTwoPeriods:
    async def test_returns_empty_when_no_data(self, db):
        repo = AlertaRepository(db)
        result = await repo.find_last_two_periods("CUATRIMESTRAL")
        assert result == []

    async def test_returns_single_period(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        await eval_repo.create(_eval(doc.id, periodo="C1 2025", año=2025, orden=1))

        result = await repo.find_last_two_periods("CUATRIMESTRAL")
        assert result == ["C1 2025"]

    async def test_returns_two_newest_periods(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)

        # C1 2024, C2 2024, C3 2024, C1 2025
        for p, y, o in [
            ("C1 2024", 2024, 1),
            ("C2 2024", 2024, 2),
            ("C3 2024", 2024, 3),
            ("C1 2025", 2025, 1),
        ]:
            await eval_repo.create(_eval(doc.id, periodo=p, año=y, orden=o))

        result = await repo.find_last_two_periods("CUATRIMESTRAL")
        assert result == ["C1 2025", "C3 2024"]

    async def test_ignores_other_modalidad(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)

        await eval_repo.create(_eval(doc.id, periodo="C1 2025", año=2025, orden=1))
        await eval_repo.create(
            _eval(doc.id, periodo="M1 2025", modalidad="MENSUAL", año=2025, orden=1)
        )

        cuatri = await repo.find_last_two_periods("CUATRIMESTRAL")
        mensual = await repo.find_last_two_periods("MENSUAL")

        assert cuatri == ["C1 2025"]
        assert mensual == ["M1 2025"]

    async def test_ignores_non_completado(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)

        ev = _eval(doc.id, periodo="C1 2025", año=2025, orden=1)
        ev.estado = "pendiente"
        await eval_repo.create(ev)

        result = await repo.find_last_two_periods("CUATRIMESTRAL")
        assert result == []


# ═══════════════════════════════════════════════════════════════════════
# load_snapshots
# ═══════════════════════════════════════════════════════════════════════


class TestLoadSnapshots:
    async def test_empty_periodos_returns_empty(self, db):
        repo = AlertaRepository(db)
        result = await repo.load_snapshots("CUATRIMESTRAL", [])
        assert result == {}

    async def test_loads_basic_snapshot(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        ev = _eval(doc.id, docente="Prof. Test", periodo="C1 2025", puntaje=72.5, materia="ISW-101")
        await eval_repo.create(ev)

        snaps = await repo.load_snapshots("CUATRIMESTRAL", ["C1 2025"])
        assert "C1 2025" in snaps
        key = ("Prof. Test", "ISW-101")
        assert key in snaps["C1 2025"]

        snap = snaps["C1 2025"][key]
        assert float(snap.puntaje_general) == 72.5
        assert snap.total_comentarios == 0
        assert snap.negativos_count == 0

    async def test_aggregates_comments(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        ev = _eval(doc.id, docente="Prof. Test", periodo="C1 2025", materia="ISW-101")
        await eval_repo.create(ev)

        # Add comments
        for kwargs in [
            {"tipo": "mejora", "sentimiento": "negativo", "tema": "metodologia"},
            {"tipo": "mejora", "sentimiento": "negativo", "tema": "actitud"},
            {"tipo": "fortaleza", "sentimiento": "positivo", "tema": "otro"},
            {"tipo": "fortaleza", "sentimiento": "negativo", "tema": "actitud"},
        ]:
            db.add(make_comentario(evaluacion_id=ev.id, **kwargs))
        await db.flush()

        snaps = await repo.load_snapshots("CUATRIMESTRAL", ["C1 2025"])
        snap = snaps["C1 2025"][("Prof. Test", "ISW-101")]

        assert snap.total_comentarios == 4
        assert snap.negativos_count == 3  # 2 mejora-neg + 1 fortaleza-neg
        assert snap.mejora_negativo_count == 2
        assert snap.actitud_negativo_count == 2  # actitud+neg (mejora + fortaleza)
        assert snap.otro_count == 1

    async def test_null_materia_becomes_sin_curso(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        ev = _eval(doc.id, materia=None)
        await eval_repo.create(ev)

        snaps = await repo.load_snapshots("CUATRIMESTRAL", ["C1 2025"])
        keys = list(snaps["C1 2025"].keys())
        assert keys[0][1] == "SIN CURSO"


# ═══════════════════════════════════════════════════════════════════════
# upsert_batch
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.requires_postgres
class TestUpsertBatch:
    async def test_empty_batch_returns_zero(self, db):
        repo = AlertaRepository(db)
        assert await repo.upsert_batch([]) == 0

    async def test_inserts_new_alerts(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        ev = _eval(doc.id)
        await eval_repo.create(ev)

        c = _candidate(eval_id=ev.id)
        rows = await repo.upsert_batch([c])
        assert rows == 1

    async def test_upsert_updates_activa_alert(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        ev = _eval(doc.id)
        await eval_repo.create(ev)

        c1 = _candidate(eval_id=ev.id)
        await repo.upsert_batch([c1])

        # Same dedup key, different value
        c2 = AlertCandidate(
            evaluacion_id=ev.id,
            docente_nombre=c1.docente_nombre,
            curso=c1.curso,
            periodo=c1.periodo,
            modalidad="CUATRIMESTRAL",
            tipo_alerta=c1.tipo_alerta,
            metrica_afectada="puntaje_general",
            valor_actual=42.0,  # changed
            valor_anterior=None,
            descripcion="Updated alert",
            severidad=Severidad.MEDIA,  # changed
        )
        rows = await repo.upsert_batch([c2])
        assert rows == 1

    async def test_no_duplicate_on_same_dedup_key(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        ev = _eval(doc.id)
        await eval_repo.create(ev)

        c = _candidate(eval_id=ev.id)
        await repo.upsert_batch([c])
        await repo.upsert_batch([c])

        count = await repo.count()
        assert count == 1

    async def test_different_tipo_creates_separate_alerts(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)
        repo = AlertaRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        ev = _eval(doc.id)
        await eval_repo.create(ev)

        c1 = _candidate(eval_id=ev.id, tipo=TipoAlerta.BAJO_DESEMPENO)
        c2 = _candidate(eval_id=ev.id, tipo=TipoAlerta.CAIDA)
        rows = await repo.upsert_batch([c1, c2])
        assert rows == 2
