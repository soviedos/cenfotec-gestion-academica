"""Dashboard service — aggregates data from multiple repositories for the executive view."""

from __future__ import annotations

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.comentario_analisis import ComentarioAnalisis
from app.domain.entities.evaluacion import Evaluacion
from app.domain.periodo import sort_periodos
from app.domain.schemas.dashboard import (
    ActividadReciente,
    AlertaDocente,
    DashboardKpis,
    DashboardSummary,
    DocenteResumen,
    InsightItem,
)

# Threshold below which a docente is considered in alert
_ALERT_THRESHOLD = 60.0


class DashboardService:
    """Builds the aggregated executive dashboard payload."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def summary(self, *, modalidad: str | None = None) -> DashboardSummary:
        kpis, docente_rows = await self._kpis_and_docentes(modalidad)
        alertas = self._build_alertas(docente_rows)
        top = self._build_ranked(docente_rows[:5])
        bottom = self._build_ranked(
            list(reversed(docente_rows[-5:])), start_pos=len(docente_rows) - 4
        )
        tendencia = await self._tendencia(modalidad)
        insights = await self._insights(modalidad)
        actividad = await self._actividad_reciente()

        return DashboardSummary(
            kpis=kpis,
            alertas=alertas,
            tendencia=tendencia,
            top_docentes=top,
            bottom_docentes=bottom,
            insights=insights,
            actividad_reciente=actividad,
        )

    # ── Private helpers ──────────────────────────────────────────────

    async def _kpis_and_docentes(
        self, modalidad: str | None = None
    ) -> tuple[DashboardKpis, list[dict]]:
        """Fetch KPIs and per-docente averages in two queries."""
        # 1. Global KPIs
        from app.domain.entities.documento import Documento

        eval_filter = [Evaluacion.estado == "completado"]
        if modalidad:
            eval_filter.append(Evaluacion.modalidad == modalidad)

        if modalidad:
            # Count only documents that have at least one evaluacion with this modalidad
            doc_count_stmt = select(func.count(func.distinct(Evaluacion.documento_id))).where(
                *eval_filter
            )
        else:
            doc_count_stmt = select(func.count(Documento.id)).where(Documento.estado == "procesado")
        docs_processed = (await self.db.execute(doc_count_stmt)).scalar() or 0

        base = select(Evaluacion).where(*eval_filter).subquery()
        kpi_stmt = select(
            func.coalesce(func.avg(base.c.puntaje_general.cast(Float)), 0.0).label("promedio"),
            func.count(func.distinct(base.c.docente_nombre)).label("docentes"),
        )
        kpi_row = (await self.db.execute(kpi_stmt)).one()

        # 2. Per-docente averages (for alerts + top/bottom)
        docente_stmt = (
            select(
                Evaluacion.docente_nombre,
                func.avg(Evaluacion.puntaje_general.cast(Float)).label("promedio"),
                func.count(Evaluacion.id).label("evaluaciones_count"),
            )
            .where(*eval_filter)
            .group_by(Evaluacion.docente_nombre)
            .order_by(func.avg(Evaluacion.puntaje_general.cast(Float)).desc())
        )
        rows = (await self.db.execute(docente_stmt)).all()
        docente_rows = [
            {
                "docente_nombre": r.docente_nombre,
                "promedio": round(float(r.promedio), 2),
                "evaluaciones_count": r.evaluaciones_count,
            }
            for r in rows
        ]

        alertas_count = sum(1 for d in docente_rows if d["promedio"] < _ALERT_THRESHOLD)

        kpis = DashboardKpis(
            documentos_procesados=docs_processed,
            docentes_evaluados=kpi_row.docentes,
            promedio_general=round(float(kpi_row.promedio), 2),
            alertas_criticas=alertas_count,
        )
        return kpis, docente_rows

    def _build_alertas(self, docente_rows: list[dict]) -> list[AlertaDocente]:
        alertas = []
        for d in docente_rows:
            if d["promedio"] < _ALERT_THRESHOLD:
                alertas.append(
                    AlertaDocente(
                        docente_nombre=d["docente_nombre"],
                        promedio=d["promedio"],
                        evaluaciones_count=d["evaluaciones_count"],
                        motivo=f"Promedio bajo ({d['promedio']}% < {_ALERT_THRESHOLD}%)",
                    )
                )
        return sorted(alertas, key=lambda a: a.promedio)[:10]

    @staticmethod
    def _build_ranked(rows: list[dict], start_pos: int = 1) -> list[DocenteResumen]:
        return [
            DocenteResumen(
                posicion=start_pos + i,
                docente_nombre=r["docente_nombre"],
                promedio=r["promedio"],
                evaluaciones_count=r["evaluaciones_count"],
            )
            for i, r in enumerate(rows)
            if r.get("docente_nombre")
        ]

    async def _tendencia(self, modalidad: str | None = None) -> list[dict]:
        eval_filter = [Evaluacion.estado == "completado"]
        if modalidad:
            eval_filter.append(Evaluacion.modalidad == modalidad)
        stmt = (
            select(
                Evaluacion.periodo,
                func.min(Evaluacion.año).label("año"),
                func.min(Evaluacion.periodo_orden).label("periodo_orden"),
                func.avg(Evaluacion.puntaje_general.cast(Float)).label("promedio"),
                func.count(Evaluacion.id).label("evaluaciones_count"),
            )
            .where(*eval_filter)
            .group_by(Evaluacion.periodo)
        )
        rows = (await self.db.execute(stmt)).all()
        unsorted = [
            {
                "periodo": r.periodo,
                "año": r.año,
                "periodo_orden": r.periodo_orden,
                "promedio": round(float(r.promedio), 2),
                "evaluaciones_count": r.evaluaciones_count,
            }
            for r in rows
        ]
        return sort_periodos(unsorted)  # [BR-AN-40]

    async def _insights(self, modalidad: str | None = None) -> list[InsightItem]:
        insights: list[InsightItem] = []

        # Build base filter: optionally join through Evaluacion for modalidad
        if modalidad:
            base_join = (
                select(
                    ComentarioAnalisis.id,
                    ComentarioAnalisis.sentimiento,
                    ComentarioAnalisis.tema,
                    ComentarioAnalisis.tipo,
                    ComentarioAnalisis.procesado_ia,
                )
                .join(Evaluacion, ComentarioAnalisis.evaluacion_id == Evaluacion.id)
                .where(Evaluacion.modalidad == modalidad)
                .subquery("ca")
            )
            total_stmt = select(func.count(base_join.c.id))
            sent_stmt = select(
                base_join.c.sentimiento,
                func.count(base_join.c.id).label("cnt"),
            ).group_by(base_join.c.sentimiento)
            tema_stmt = (
                select(
                    base_join.c.tema,
                    func.count(base_join.c.id).label("cnt"),
                )
                .group_by(base_join.c.tema)
                .order_by(func.count(base_join.c.id).desc())
                .limit(3)
            )
            ia_stmt = select(func.count(base_join.c.id)).where(base_join.c.procesado_ia.is_(True))
        else:
            total_stmt = select(func.count(ComentarioAnalisis.id))
            sent_stmt = select(
                ComentarioAnalisis.sentimiento,
                func.count(ComentarioAnalisis.id).label("cnt"),
            ).group_by(ComentarioAnalisis.sentimiento)
            tema_stmt = (
                select(
                    ComentarioAnalisis.tema,
                    func.count(ComentarioAnalisis.id).label("cnt"),
                )
                .group_by(ComentarioAnalisis.tema)
                .order_by(func.count(ComentarioAnalisis.id).desc())
                .limit(3)
            )
            ia_stmt = select(func.count(ComentarioAnalisis.id)).where(
                ComentarioAnalisis.procesado_ia.is_(True)
            )

        # Sentiment distribution
        total = (await self.db.execute(total_stmt)).scalar() or 0
        if total == 0:
            return [InsightItem(icono="info", texto="Aún no hay comentarios analizados.")]

        sent_rows = (await self.db.execute(sent_stmt)).all()
        sent_map = {r[0]: r[1] for r in sent_rows}

        positivos = sent_map.get("positivo", 0)
        negativos = sent_map.get("negativo", 0)
        pct_pos = round(positivos / total * 100, 1) if total else 0
        pct_neg = round(negativos / total * 100, 1) if total else 0

        insights.append(
            InsightItem(
                icono="sentiment",
                texto=(
                    f"{pct_pos}% de comentarios son positivos, "
                    f"{pct_neg}% negativos ({total:,} total)."
                ),
            )
        )

        # Top themes
        tema_rows = (await self.db.execute(tema_stmt)).all()
        if tema_rows:
            temas_text = ", ".join(f"{r[0]} ({r[1]})" for r in tema_rows)
            insights.append(
                InsightItem(icono="topic", texto=f"Temas más frecuentes: {temas_text}.")
            )

        # Gemini enrichment progress
        ia_count = (await self.db.execute(ia_stmt)).scalar() or 0
        pct_ia = round(ia_count / total * 100, 1) if total else 0
        insights.append(
            InsightItem(
                icono="ai",
                texto=f"{ia_count:,} de {total:,} comentarios enriquecidos por IA ({pct_ia}%).",
            )
        )

        return insights

    async def _actividad_reciente(self) -> list[ActividadReciente]:
        from app.domain.entities.documento import Documento

        stmt = (
            select(
                Documento.nombre_archivo,
                Documento.estado,
                Documento.created_at,
                func.count(Evaluacion.id).label("evaluaciones_count"),
            )
            .outerjoin(Evaluacion, Evaluacion.documento_id == Documento.id)
            .group_by(
                Documento.id, Documento.nombre_archivo, Documento.estado, Documento.created_at
            )
            .order_by(Documento.created_at.desc())
            .limit(8)
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            ActividadReciente(
                documento_nombre=r.nombre_archivo,
                estado=r.estado,
                evaluaciones_extraidas=r.evaluaciones_count,
                fecha=r.created_at.isoformat(),
            )
            for r in rows
        ]
