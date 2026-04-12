"""Alerta repository — persistence for the alert engine.

Provides:
*  ``find_last_two_periods`` — [AL-01] temporal scoping per modalidad.
*  ``load_snapshots`` — bulk-load aggregated data for detectors.
*  ``upsert_batch`` — [AL-40] INSERT … ON CONFLICT DO UPDATE.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import String, case, func, literal, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domain.alert_rules import AlertCandidate, DocenteCursoSnapshot
from app.domain.entities.alerta import Alerta
from app.domain.entities.comentario_analisis import ComentarioAnalisis
from app.domain.entities.evaluacion import Evaluacion
from app.infrastructure.repositories.base import BaseRepository


class AlertaRepository(BaseRepository[Alerta]):
    model = Alerta

    # ── Temporal scoping [AL-01] ─────────────────────────────────────

    async def find_last_two_periods(self, modalidad: str) -> list[str]:
        """Return the last 1-2 periodo strings for *modalidad*, newest first.

        Uses ``(año DESC, periodo_orden DESC)`` ordering which is backed
        by the ``ix_evaluaciones_modalidad_año_orden`` index.
        """
        stmt = (
            select(Evaluacion.periodo)
            .where(
                Evaluacion.estado == "completado",
                Evaluacion.modalidad == modalidad,
            )
            .group_by(Evaluacion.periodo, Evaluacion.año, Evaluacion.periodo_orden)
            .order_by(Evaluacion.año.desc(), Evaluacion.periodo_orden.desc())
            .limit(2)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Snapshot loading ─────────────────────────────────────────────

    async def load_snapshots(
        self,
        modalidad: str,
        periodos: Sequence[str],
    ) -> dict[str, dict[tuple[str, str], DocenteCursoSnapshot]]:
        """Load pre-aggregated snapshots for each periodo.

        Returns ``{periodo: {(docente, curso): snapshot, …}, …}``.

        A single query with ``GROUP BY`` + conditional aggregation avoids
        N+1 queries against ``comentario_analisis``.  Multiple evaluations
        for the same docente+curso+periodo are aggregated (AVG puntaje,
        SUM comment counts).
        """
        if not periodos:
            return {}

        # Sub-query: comment aggregation per evaluacion
        neg = func.count(
            case(
                (ComentarioAnalisis.sentimiento == "negativo", literal(1)),
            )
        )
        mejora_neg = func.count(
            case(
                (
                    (ComentarioAnalisis.tipo == "mejora")
                    & (ComentarioAnalisis.sentimiento == "negativo"),
                    literal(1),
                ),
            )
        )
        actitud_neg = func.count(
            case(
                (
                    (ComentarioAnalisis.tema == "actitud")
                    & (ComentarioAnalisis.sentimiento == "negativo"),
                    literal(1),
                ),
            )
        )
        otro = func.count(
            case(
                (ComentarioAnalisis.tema == "otro", literal(1)),
            )
        )
        total_com = func.count(ComentarioAnalisis.id)

        comment_agg = (
            select(
                ComentarioAnalisis.evaluacion_id.label("eval_id"),
                total_com.label("total_comentarios"),
                neg.label("negativos_count"),
                mejora_neg.label("mejora_negativo_count"),
                actitud_neg.label("actitud_negativo_count"),
                otro.label("otro_count"),
            )
            .group_by(ComentarioAnalisis.evaluacion_id)
            .subquery("ca")
        )

        # Main query: evaluaciones LEFT JOIN comment_agg
        # GROUP BY docente+curso+periodo+modalidad to aggregate multiple
        # evaluations for the same combination [AL-10].
        stmt = (
            select(
                func.max(Evaluacion.id.cast(String)).label("evaluacion_id"),
                Evaluacion.docente_nombre,
                func.coalesce(Evaluacion.materia, literal("SIN CURSO")).label("curso"),
                Evaluacion.periodo,
                Evaluacion.modalidad,
                func.avg(Evaluacion.puntaje_general).label("puntaje_general"),
                func.coalesce(func.sum(comment_agg.c.total_comentarios), 0).label(
                    "total_comentarios"
                ),
                func.coalesce(func.sum(comment_agg.c.negativos_count), 0).label("negativos_count"),
                func.coalesce(func.sum(comment_agg.c.mejora_negativo_count), 0).label(
                    "mejora_negativo_count"
                ),
                func.coalesce(func.sum(comment_agg.c.actitud_negativo_count), 0).label(
                    "actitud_negativo_count"
                ),
                func.coalesce(func.sum(comment_agg.c.otro_count), 0).label("otro_count"),
            )
            .outerjoin(comment_agg, Evaluacion.id == comment_agg.c.eval_id)
            .where(
                Evaluacion.estado == "completado",
                Evaluacion.modalidad == modalidad,
                Evaluacion.periodo.in_(periodos),
            )
            .group_by(
                Evaluacion.docente_nombre,
                Evaluacion.materia,
                Evaluacion.periodo,
                Evaluacion.modalidad,
            )
        )
        result = await self.session.execute(stmt)

        snapshots: dict[str, dict[tuple[str, str], DocenteCursoSnapshot]] = {
            p: {} for p in periodos
        }

        for row in result.mappings():
            curso = row["curso"]
            snap = DocenteCursoSnapshot(
                evaluacion_id=uuid.UUID(row["evaluacion_id"]),
                docente_nombre=row["docente_nombre"],
                curso=curso,
                periodo=row["periodo"],
                modalidad=row["modalidad"],
                puntaje_general=(
                    float(row["puntaje_general"]) if row["puntaje_general"] is not None else None
                ),
                total_comentarios=int(row["total_comentarios"]),
                negativos_count=int(row["negativos_count"]),
                mejora_negativo_count=int(row["mejora_negativo_count"]),
                actitud_negativo_count=int(row["actitud_negativo_count"]),
                otro_count=int(row["otro_count"]),
            )
            key = (snap.docente_nombre, snap.curso)
            snapshots[snap.periodo][key] = snap

        return snapshots

    # ── Upsert [AL-40] ──────────────────────────────────────────────

    async def upsert_batch(self, candidates: Sequence[AlertCandidate]) -> int:
        """Insert or update alerts in bulk.  Returns rows affected.

        Uses PostgreSQL ``ON CONFLICT … DO UPDATE`` on the dedup
        constraint.  Only rows still in ``estado='activa'`` are updated;
        alerts already reviewed/resolved keep their lifecycle state.
        """
        if not candidates:
            return 0

        values = [
            {
                "id": uuid.uuid4(),
                "evaluacion_id": c.evaluacion_id,
                "docente_nombre": c.docente_nombre,
                "curso": c.curso,
                "periodo": c.periodo,
                "tipo_alerta": c.tipo_alerta.value,
                "modalidad": c.modalidad,
                "metrica_afectada": c.metrica_afectada,
                "valor_actual": c.valor_actual,
                "valor_anterior": c.valor_anterior,
                "descripcion": c.descripcion,
                "severidad": c.severidad.value,
                "estado": "activa",
            }
            for c in candidates
        ]

        stmt = pg_insert(Alerta).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_alertas_dedup",
            set_={
                "evaluacion_id": stmt.excluded.evaluacion_id,
                "modalidad": stmt.excluded.modalidad,
                "metrica_afectada": stmt.excluded.metrica_afectada,
                "valor_actual": stmt.excluded.valor_actual,
                "valor_anterior": stmt.excluded.valor_anterior,
                "descripcion": stmt.excluded.descripcion,
                "severidad": stmt.excluded.severidad,
                "updated_at": text("now()"),
            },
            where=(Alerta.estado == "activa"),
        )

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    # ── Query methods (for API endpoints) ────────────────────────────

    async def list_filtered(
        self,
        *,
        modalidad: str | None = None,
        año: int | None = None,
        periodo: str | None = None,
        severidad: str | None = None,
        estado: str | None = None,
        docente: str | None = None,
        curso: str | None = None,
        tipo_alerta: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Alerta], int]:
        """Return filtered alerts with total count for pagination."""
        base = select(Alerta)
        count_stmt = select(func.count()).select_from(Alerta)

        filters = self._build_filters(
            modalidad=modalidad,
            año=año,
            periodo=periodo,
            severidad=severidad,
            estado=estado,
            docente=docente,
            curso=curso,
            tipo_alerta=tipo_alerta,
        )
        for f in filters:
            base = base.where(f)
            count_stmt = count_stmt.where(f)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        items_stmt = base.order_by(Alerta.created_at.desc()).offset(offset).limit(limit)
        items_result = await self.session.execute(items_stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def summary(self, *, estado: str = "activa", modalidad: str | None = None) -> dict:
        """Aggregate counts for the dashboard summary card."""
        base_filters = [Alerta.estado == estado]
        if modalidad:
            base_filters.append(Alerta.modalidad == modalidad)

        # Total
        total_stmt = select(func.count()).select_from(Alerta).where(*base_filters)
        total = (await self.session.execute(total_stmt)).scalar_one()

        # By severidad
        sev_stmt = (
            select(Alerta.severidad, func.count()).where(*base_filters).group_by(Alerta.severidad)
        )
        sev_rows = (await self.session.execute(sev_stmt)).all()
        por_severidad = {row[0]: row[1] for row in sev_rows}

        # By tipo_alerta
        tipo_stmt = (
            select(Alerta.tipo_alerta, func.count())
            .where(*base_filters)
            .group_by(Alerta.tipo_alerta)
        )
        tipo_rows = (await self.session.execute(tipo_stmt)).all()
        por_tipo = {row[0]: row[1] for row in tipo_rows}

        # By modalidad
        mod_stmt = (
            select(Alerta.modalidad, func.count()).where(*base_filters).group_by(Alerta.modalidad)
        )
        mod_rows = (await self.session.execute(mod_stmt)).all()
        por_modalidad = {row[0]: row[1] for row in mod_rows}

        # Distinct docentes affected
        doc_stmt = select(func.count(func.distinct(Alerta.docente_nombre))).where(*base_filters)
        docentes = (await self.session.execute(doc_stmt)).scalar_one()

        return {
            "total_activas": total,
            "por_severidad": por_severidad,
            "por_tipo": por_tipo,
            "por_modalidad": por_modalidad,
            "docentes_afectados": docentes,
        }

    async def update_estado(self, alerta_id: uuid.UUID, nuevo_estado: str) -> Alerta | None:
        """Transition alert lifecycle state [AL-50]."""
        alerta = await self.get_by_id(alerta_id)
        if alerta is None:
            return None
        alerta.estado = nuevo_estado
        await self.session.flush()
        await self.session.refresh(alerta)
        return alerta

    # ── Private helpers ──────────────────────────────────────────────

    @staticmethod
    def _build_filters(
        *,
        modalidad: str | None,
        año: int | None,
        periodo: str | None,
        severidad: str | None,
        estado: str | None,
        docente: str | None,
        curso: str | None,
        tipo_alerta: str | None,
    ) -> list:
        filters = []
        if modalidad:
            filters.append(Alerta.modalidad == modalidad)
        if periodo:
            filters.append(Alerta.periodo == periodo)
        if severidad:
            filters.append(Alerta.severidad == severidad)
        if estado:
            filters.append(Alerta.estado == estado)
        if docente:
            filters.append(Alerta.docente_nombre.ilike(f"%{docente}%"))
        if curso:
            filters.append(Alerta.curso.ilike(f"%{curso}%"))
        if tipo_alerta:
            filters.append(Alerta.tipo_alerta == tipo_alerta)
        if año:
            filters.append(Alerta.periodo.like(f"%{año}%"))
        return filters
