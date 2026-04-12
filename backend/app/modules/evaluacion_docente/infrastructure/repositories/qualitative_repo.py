"""Read-only qualitative analytics repository — aggregate queries for comments."""

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import JSON, Float, String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.domain.entities.comentario_analisis import ComentarioAnalisis
from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion

# Stop-words to exclude from word cloud
_STOPWORDS = frozenset(
    "el la los las un una unos unas de del al a en con por para su sus "
    "es son fue ser no si lo le se que y o el del más muy como pero "
    "todo toda todos todas este esta estos estas ese esa esos esas "
    "me te nos les mi tu hay ya también entre sobre hasta sin embargo "
    "bien mal mucho poco cuando tiene cada uno era han ha".split()
)
_WORD_RE = re.compile(r"[a-záéíóúñü]{3,}", re.IGNORECASE)


class QualitativeRepository:
    """Aggregate read queries for qualitative/sentiment endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _recinto_col():
        """Column expression for ``datos_completos -> 'header' -> 'recinto'``.

        Uses SQLAlchemy's JSON type operations so the query is
        dialect-portable (PostgreSQL JSONB).
        """
        return cast(Evaluacion.datos_completos, JSON)["header"]["recinto"].as_string()

    # ── Helpers ──────────────────────────────────────────────────────

    def _base_query(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        modalidad: str | None = None,
        tipo: str | None = None,
        tema: str | None = None,
        sentimiento: str | None = None,
    ):
        """Build a filtered base select on ComentarioAnalisis."""
        stmt = select(ComentarioAnalisis)

        if periodo or docente or escuela or modalidad:
            stmt = stmt.join(Evaluacion, ComentarioAnalisis.evaluacion_id == Evaluacion.id)
            if periodo:
                stmt = stmt.where(Evaluacion.periodo == periodo)
            if docente:
                stmt = stmt.where(Evaluacion.docente_nombre == docente)
            if escuela:
                stmt = stmt.where(self._recinto_col().ilike(f"%{escuela}%"))
            if modalidad:
                stmt = stmt.where(Evaluacion.modalidad == modalidad)

        if asignatura:
            stmt = stmt.where(ComentarioAnalisis.asignatura == asignatura)
        if tipo:
            stmt = stmt.where(ComentarioAnalisis.tipo == tipo)
        if tema:
            stmt = stmt.where(ComentarioAnalisis.tema == tema)
        if sentimiento:
            stmt = stmt.where(ComentarioAnalisis.sentimiento == sentimiento)

        return stmt

    # ── 1. Resumen cualitativo ──────────────────────────────────────

    async def filtros_disponibles(self) -> dict:
        """Return distinct filter option values."""
        # Periodos (from evaluaciones join)
        p_stmt = (
            select(Evaluacion.periodo)
            .join(ComentarioAnalisis, ComentarioAnalisis.evaluacion_id == Evaluacion.id)
            .distinct()
            .order_by(Evaluacion.periodo)
        )
        periodos = [r[0] for r in (await self.session.execute(p_stmt)).all()]

        # Docentes
        d_stmt = (
            select(Evaluacion.docente_nombre)
            .join(ComentarioAnalisis, ComentarioAnalisis.evaluacion_id == Evaluacion.id)
            .distinct()
            .order_by(Evaluacion.docente_nombre)
        )
        docentes = [r[0] for r in (await self.session.execute(d_stmt)).all()]

        # Asignaturas
        a_stmt = (
            select(ComentarioAnalisis.asignatura).distinct().order_by(ComentarioAnalisis.asignatura)
        )
        asignaturas = [r[0] for r in (await self.session.execute(a_stmt)).all()]

        # Escuelas (from datos_completos JSON -> header.recinto)
        recinto = self._recinto_col()
        e_stmt = (
            select(func.replace(recinto, "TODOS, ", "").label("escuela"))
            .select_from(Evaluacion)
            .join(ComentarioAnalisis, ComentarioAnalisis.evaluacion_id == Evaluacion.id)
            .where(recinto.isnot(None))
            .distinct()
        )
        escuelas = sorted([r[0] for r in (await self.session.execute(e_stmt)).all() if r[0]])

        return {
            "periodos": periodos,
            "docentes": docentes,
            "asignaturas": asignaturas,
            "escuelas": escuelas,
        }

    async def resumen(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        modalidad: str | None = None,
    ) -> dict:
        """Return qualitative summary metrics."""
        base = self._base_query(
            periodo=periodo,
            docente=docente,
            asignatura=asignatura,
            escuela=escuela,
            modalidad=modalidad,
        ).subquery()

        total_stmt = select(func.count(base.c.id))
        total = (await self.session.execute(total_stmt)).scalar() or 0

        if total == 0:
            return {
                "total_comentarios": 0,
                "por_tipo": [],
                "por_sentimiento": [],
                "temas_top": [],
                "sentimiento_promedio": None,
            }

        # por tipo
        tipo_stmt = (
            select(
                base.c.tipo,
                func.count(base.c.id).label("count"),
            )
            .group_by(base.c.tipo)
            .order_by(func.count(base.c.id).desc())
        )
        tipo_rows = (await self.session.execute(tipo_stmt)).all()

        # por sentimiento
        sent_stmt = (
            select(
                base.c.sentimiento,
                func.count(base.c.id).label("count"),
            )
            .group_by(base.c.sentimiento)
            .order_by(func.count(base.c.id).desc())
        )
        sent_rows = (await self.session.execute(sent_stmt)).all()

        # temas top
        tema_stmt = (
            select(
                base.c.tema,
                func.count(base.c.id).label("count"),
            )
            .group_by(base.c.tema)
            .order_by(func.count(base.c.id).desc())
            .limit(10)
        )
        tema_rows = (await self.session.execute(tema_stmt)).all()

        # sentimiento promedio
        avg_stmt = select(func.avg(base.c.sent_score.cast(Float)))
        avg_sent = (await self.session.execute(avg_stmt)).scalar()

        return {
            "total_comentarios": total,
            "por_tipo": [{"tipo": r.tipo, "count": r.count} for r in tipo_rows],
            "por_sentimiento": [
                {
                    "sentimiento": r.sentimiento or "sin_clasificar",
                    "count": r.count,
                    "porcentaje": round(r.count / total * 100, 1),
                }
                for r in sent_rows
            ],
            "temas_top": [
                {
                    "tema": r.tema,
                    "count": r.count,
                    "porcentaje": round(r.count / total * 100, 1),
                }
                for r in tema_rows
            ],
            "sentimiento_promedio": round(float(avg_sent), 2) if avg_sent is not None else None,
        }

    # ── 2. Lista de comentarios (paginada) ──────────────────────────

    async def listar_comentarios(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        modalidad: str | None = None,
        tipo: str | None = None,
        tema: str | None = None,
        sentimiento: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComentarioAnalisis]:
        """Return filtered, paginated list of comment records."""
        stmt = (
            self._base_query(
                periodo=periodo,
                docente=docente,
                asignatura=asignatura,
                escuela=escuela,
                modalidad=modalidad,
                tipo=tipo,
                tema=tema,
                sentimiento=sentimiento,
            )
            .order_by(ComentarioAnalisis.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def contar_comentarios(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        modalidad: str | None = None,
        tipo: str | None = None,
        tema: str | None = None,
        sentimiento: str | None = None,
    ) -> int:
        """Count filtered comments."""
        sub = self._base_query(
            periodo=periodo,
            docente=docente,
            asignatura=asignatura,
            escuela=escuela,
            modalidad=modalidad,
            tipo=tipo,
            tema=tema,
            sentimiento=sentimiento,
        ).subquery()
        stmt = select(func.count(sub.c.id))
        return (await self.session.execute(stmt)).scalar() or 0

    # ── 3. Distribución por tema ────────────────────────────────────

    async def distribucion_temas(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        modalidad: str | None = None,
        tipo: str | None = None,
    ) -> list[dict]:
        """Return comment count per tema."""
        sub = self._base_query(
            periodo=periodo,
            docente=docente,
            asignatura=asignatura,
            escuela=escuela,
            modalidad=modalidad,
            tipo=tipo,
        ).subquery()

        total_stmt = select(func.count(sub.c.id))
        total = (await self.session.execute(total_stmt)).scalar() or 0
        if total == 0:
            return []

        stmt = (
            select(
                sub.c.tema,
                func.count(sub.c.id).label("count"),
            )
            .group_by(sub.c.tema)
            .order_by(func.count(sub.c.id).desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "tema": r.tema,
                "count": r.count,
                "porcentaje": round(r.count / total * 100, 1),
            }
            for r in rows
        ]

    # ── 4. Distribución por sentimiento ─────────────────────────────

    async def distribucion_sentimiento(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        modalidad: str | None = None,
        tipo: str | None = None,
        tema: str | None = None,
    ) -> list[dict]:
        """Return comment count per sentimiento."""
        sub = self._base_query(
            periodo=periodo,
            docente=docente,
            asignatura=asignatura,
            escuela=escuela,
            modalidad=modalidad,
            tipo=tipo,
            tema=tema,
        ).subquery()

        total_stmt = select(func.count(sub.c.id))
        total = (await self.session.execute(total_stmt)).scalar() or 0
        if total == 0:
            return []

        stmt = (
            select(
                sub.c.sentimiento.cast(String).label("sentimiento"),
                func.count(sub.c.id).label("count"),
            )
            .group_by(sub.c.sentimiento)
            .order_by(func.count(sub.c.id).desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "sentimiento": r.sentimiento or "sin_clasificar",
                "count": r.count,
                "porcentaje": round(r.count / total * 100, 1),
            }
            for r in rows
        ]

    # ── 5. Nube de palabras ─────────────────────────────────────────

    async def nube_palabras(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        modalidad: str | None = None,
        tipo: str | None = None,
        top_n: int = 60,
    ) -> list[dict]:
        """Return word frequencies from comment texts.

        Only the most recent ``_MAX_TEXTS`` comments are loaded into
        memory to prevent OOM with large datasets.
        """
        max_texts = 2000

        sub = self._base_query(
            periodo=periodo,
            docente=docente,
            asignatura=asignatura,
            escuela=escuela,
            modalidad=modalidad,
            tipo=tipo,
        ).subquery()

        stmt = select(sub.c.texto).order_by(sub.c.created_at.desc()).limit(max_texts)
        rows = (await self.session.execute(stmt)).all()

        counter: Counter[str] = Counter()
        for (texto,) in rows:
            words = _WORD_RE.findall(texto.lower())
            counter.update(w for w in words if w not in _STOPWORDS)

        return [{"text": word, "value": count} for word, count in counter.most_common(top_n)]
