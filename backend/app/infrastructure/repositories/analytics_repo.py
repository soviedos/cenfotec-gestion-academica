"""Read-only analytics repository — aggregate queries for the BI dashboard.

This repository does NOT extend ``BaseRepository`` because it only performs
read operations (no CRUD).  All methods return raw dicts/tuples that the
service layer maps to Pydantic schemas.
"""

from __future__ import annotations

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.evaluacion import Evaluacion
from app.domain.entities.evaluacion_curso import EvaluacionCurso
from app.domain.entities.evaluacion_dimension import EvaluacionDimension
from app.domain.periodo import sort_periodos


def _curso_filter_subquery(
    escuela: str | None = None,
    curso: str | None = None,
):
    """Return a subquery of evaluacion_ids matching escuela/curso criteria."""
    sq = select(EvaluacionCurso.evaluacion_id)
    if escuela:
        sq = sq.where(EvaluacionCurso.escuela == escuela)
    if curso:
        sq = sq.where(EvaluacionCurso.nombre == curso)
    return sq


class AnalyticsRepository:
    """Aggregate read queries for analytics endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── 1. Resumen general ──────────────────────────────────────────

    async def resumen_global(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
    ) -> dict:
        """Return global summary metrics.

        Returns dict with keys: promedio_global, total_evaluaciones,
        total_docentes, total_periodos.
        """
        base = select(Evaluacion).where(Evaluacion.estado == "completado")
        if periodo:
            base = base.where(Evaluacion.periodo == periodo)
        if modalidad:
            base = base.where(Evaluacion.modalidad == modalidad)
        if escuela or curso:
            base = base.where(Evaluacion.id.in_(_curso_filter_subquery(escuela, curso)))

        sub = base.subquery()

        avg_expr = func.coalesce(func.avg(sub.c.puntaje_general.cast(Float)), 0.0).label(
            "promedio_global"
        )
        stmt = select(
            avg_expr,
            func.count(sub.c.id).label("total_evaluaciones"),
            func.count(func.distinct(sub.c.docente_nombre)).label("total_docentes"),
            func.count(func.distinct(sub.c.periodo)).label("total_periodos"),
        )
        row = (await self.session.execute(stmt)).one()
        return {
            "promedio_global": round(float(row.promedio_global), 2),
            "total_evaluaciones": row.total_evaluaciones,
            "total_docentes": row.total_docentes,
            "total_periodos": row.total_periodos,
        }

    # ── 2. Promedio por docente ─────────────────────────────────────

    async def promedios_por_docente(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Return average score per teacher."""
        stmt = (
            select(
                Evaluacion.docente_nombre,
                func.avg(Evaluacion.puntaje_general.cast(Float)).label("promedio"),
                func.count(Evaluacion.id).label("evaluaciones_count"),
            )
            .where(Evaluacion.estado == "completado")
            .group_by(Evaluacion.docente_nombre)
            .order_by(func.avg(Evaluacion.puntaje_general.cast(Float)).desc())
        )
        if periodo:
            stmt = stmt.where(Evaluacion.periodo == periodo)
        if modalidad:
            stmt = stmt.where(Evaluacion.modalidad == modalidad)
        if escuela or curso:
            stmt = stmt.where(Evaluacion.id.in_(_curso_filter_subquery(escuela, curso)))
        stmt = stmt.offset(offset).limit(limit)

        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "docente_nombre": r.docente_nombre,
                "promedio": round(float(r.promedio), 2),
                "evaluaciones_count": r.evaluaciones_count,
            }
            for r in rows
        ]

    # ── 3. Promedio por dimensión (radar) ───────────────────────────

    async def promedios_por_dimension(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
    ) -> list[dict]:
        """Return average percentages per evaluation dimension.

        Always JOINs to Evaluacion to guarantee ``estado='completado'``
        and proper modalidad isolation [BR-AN-01].
        """
        stmt = (
            select(
                EvaluacionDimension.nombre.label("dimension"),
                func.avg(EvaluacionDimension.pct_estudiante.cast(Float)).label("pct_estudiante"),
                func.avg(EvaluacionDimension.pct_director.cast(Float)).label("pct_director"),
                func.avg(EvaluacionDimension.pct_autoeval.cast(Float)).label("pct_autoeval"),
                func.avg(EvaluacionDimension.pct_promedio.cast(Float)).label("pct_promedio"),
            )
            .join(Evaluacion, EvaluacionDimension.evaluacion_id == Evaluacion.id)
            .where(Evaluacion.estado == "completado")
            .group_by(EvaluacionDimension.nombre)
            .order_by(EvaluacionDimension.nombre)
        )

        if periodo:
            stmt = stmt.where(Evaluacion.periodo == periodo)
        if docente:
            stmt = stmt.where(Evaluacion.docente_nombre == docente)
        if modalidad:
            stmt = stmt.where(Evaluacion.modalidad == modalidad)
        if escuela or curso:
            stmt = stmt.where(Evaluacion.id.in_(_curso_filter_subquery(escuela, curso)))

        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "dimension": r.dimension,
                "pct_estudiante": round(float(r.pct_estudiante), 2) if r.pct_estudiante else None,
                "pct_director": round(float(r.pct_director), 2) if r.pct_director else None,
                "pct_autoeval": round(float(r.pct_autoeval), 2) if r.pct_autoeval else None,
                "pct_promedio": round(float(r.pct_promedio), 2) if r.pct_promedio else None,
            }
            for r in rows
        ]

    # ── 4. Evolución por período ────────────────────────────────────

    async def evolucion_periodos(
        self,
        *,
        docente: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
    ) -> list[dict]:
        """Return average score per period for trend analysis."""
        stmt = (
            select(
                Evaluacion.periodo,
                func.min(Evaluacion.modalidad).label("modalidad"),
                func.avg(Evaluacion.puntaje_general.cast(Float)).label("promedio"),
                func.count(Evaluacion.id).label("evaluaciones_count"),
            )
            .where(Evaluacion.estado == "completado")
            .group_by(Evaluacion.periodo)
        )
        if docente:
            stmt = stmt.where(Evaluacion.docente_nombre == docente)
        if modalidad:
            stmt = stmt.where(Evaluacion.modalidad == modalidad)
        if escuela or curso:
            stmt = stmt.where(Evaluacion.id.in_(_curso_filter_subquery(escuela, curso)))

        rows = (await self.session.execute(stmt)).all()
        unsorted = [
            {
                "periodo": r.periodo,
                "modalidad": r.modalidad,
                "promedio": round(float(r.promedio), 2),
                "evaluaciones_count": r.evaluaciones_count,
            }
            for r in rows
        ]
        return sort_periodos(unsorted)  # [BR-AN-40]

    # ── 5. Ranking de docentes ──────────────────────────────────────

    async def ranking_docentes(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Return top teachers ranked by average score."""
        stmt = (
            select(
                Evaluacion.docente_nombre,
                func.avg(Evaluacion.puntaje_general.cast(Float)).label("promedio"),
                func.count(Evaluacion.id).label("evaluaciones_count"),
            )
            .where(Evaluacion.estado == "completado")
            .group_by(Evaluacion.docente_nombre)
            .order_by(func.avg(Evaluacion.puntaje_general.cast(Float)).desc())
            .limit(limit)
        )
        if periodo:
            stmt = stmt.where(Evaluacion.periodo == periodo)
        if modalidad:
            stmt = stmt.where(Evaluacion.modalidad == modalidad)
        if escuela or curso:
            stmt = stmt.where(Evaluacion.id.in_(_curso_filter_subquery(escuela, curso)))

        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "posicion": idx + 1,
                "docente_nombre": r.docente_nombre,
                "promedio": round(float(r.promedio), 2),
                "evaluaciones_count": r.evaluaciones_count,
            }
            for idx, r in enumerate(rows)
        ]

    # ── 6. Distinct escuelas ────────────────────────────────────────

    async def distinct_escuelas(
        self,
        *,
        modalidad: str | None = None,
        periodo: str | None = None,
    ) -> list[str]:
        """Return sorted list of distinct escuelas."""
        stmt = select(func.distinct(EvaluacionCurso.escuela)).where(
            EvaluacionCurso.escuela.isnot(None)
        )
        if modalidad or periodo:
            stmt = stmt.join(Evaluacion, EvaluacionCurso.evaluacion_id == Evaluacion.id)
            stmt = stmt.where(Evaluacion.estado == "completado")
            if modalidad:
                stmt = stmt.where(Evaluacion.modalidad == modalidad)
            if periodo:
                stmt = stmt.where(Evaluacion.periodo == periodo)
        rows = (await self.session.execute(stmt)).scalars().all()
        return sorted(rows)

    # ── 7. Distinct cursos ──────────────────────────────────────────

    async def distinct_cursos(
        self,
        *,
        escuela: str | None = None,
        modalidad: str | None = None,
        periodo: str | None = None,
    ) -> list[str]:
        """Return sorted list of distinct curso names."""
        stmt = select(func.distinct(EvaluacionCurso.nombre)).where(
            EvaluacionCurso.nombre.isnot(None)
        )
        if escuela:
            stmt = stmt.where(EvaluacionCurso.escuela == escuela)
        if modalidad or periodo:
            stmt = stmt.join(Evaluacion, EvaluacionCurso.evaluacion_id == Evaluacion.id)
            stmt = stmt.where(Evaluacion.estado == "completado")
            if modalidad:
                stmt = stmt.where(Evaluacion.modalidad == modalidad)
            if periodo:
                stmt = stmt.where(Evaluacion.periodo == periodo)
        rows = (await self.session.execute(stmt)).scalars().all()
        return sorted(rows)

    # ── 8. Distinct periodos ────────────────────────────────────────

    async def distinct_periodos(
        self,
        *,
        modalidad: str | None = None,
    ) -> list[dict]:
        """Return distinct periodos with their modalidad, sorted chronologically."""
        stmt = (
            select(
                Evaluacion.periodo,
                func.min(Evaluacion.modalidad).label("modalidad"),
            )
            .where(Evaluacion.estado == "completado")
            .group_by(Evaluacion.periodo)
        )
        if modalidad:
            stmt = stmt.where(Evaluacion.modalidad == modalidad)
        rows = (await self.session.execute(stmt)).all()
        unsorted = [{"periodo": r.periodo, "modalidad": r.modalidad} for r in rows]
        return sort_periodos(unsorted)
