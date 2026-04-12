"""Analytics service — thin business layer for BI dashboard queries."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.domain.schemas.analytics import (
    DimensionPromedio,
    DocentePromedio,
    PeriodoMetrica,
    PeriodoOption,
    RankingDocente,
    ResumenGeneral,
)
from app.modules.evaluacion_docente.infrastructure.repositories.analytics_repo import (
    AnalyticsRepository,
)
from app.shared.core.cache import analytics_cache


class AnalyticsService:
    """Delegates to :class:`AnalyticsRepository` and maps results to schemas.

    Results are cached in-memory for 5 minutes to reduce DB load on
    repeated dashboard visits.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AnalyticsRepository(db)

    async def resumen(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
    ) -> ResumenGeneral:
        key = f"analytics:resumen:{modalidad}:{periodo}:{escuela}:{curso}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return ResumenGeneral(**cached)
        data = await self.repo.resumen_global(
            periodo=periodo,
            modalidad=modalidad,
            escuela=escuela,
            curso=curso,
        )
        result = ResumenGeneral(**data)
        await analytics_cache.set(key, result.model_dump())
        return result

    async def promedios_docentes(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DocentePromedio]:
        key = f"analytics:docentes:{modalidad}:{periodo}:{escuela}:{curso}:{limit}:{offset}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [DocentePromedio(**r) for r in cached]
        rows = await self.repo.promedios_por_docente(
            periodo=periodo,
            modalidad=modalidad,
            escuela=escuela,
            curso=curso,
            limit=limit,
            offset=offset,
        )
        result = [DocentePromedio(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result

    async def dimensiones(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
    ) -> list[DimensionPromedio]:
        key = f"analytics:dimensiones:{modalidad}:{periodo}:{docente}:{escuela}:{curso}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [DimensionPromedio(**r) for r in cached]
        rows = await self.repo.promedios_por_dimension(
            periodo=periodo,
            docente=docente,
            modalidad=modalidad,
            escuela=escuela,
            curso=curso,
        )
        result = [DimensionPromedio(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result

    async def evolucion(
        self,
        *,
        docente: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
    ) -> list[PeriodoMetrica]:
        key = f"analytics:evolucion:{modalidad}:{docente}:{escuela}:{curso}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [PeriodoMetrica(**r) for r in cached]
        rows = await self.repo.evolucion_periodos(
            docente=docente,
            modalidad=modalidad,
            escuela=escuela,
            curso=curso,
        )
        result = [PeriodoMetrica(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result

    async def ranking(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        escuela: str | None = None,
        curso: str | None = None,
        limit: int = 10,
    ) -> list[RankingDocente]:
        key = f"analytics:ranking:{modalidad}:{periodo}:{escuela}:{curso}:{limit}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [RankingDocente(**r) for r in cached]
        rows = await self.repo.ranking_docentes(
            periodo=periodo,
            modalidad=modalidad,
            escuela=escuela,
            curso=curso,
            limit=limit,
        )
        result = [RankingDocente(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result

    async def escuelas(
        self,
        *,
        modalidad: str | None = None,
        periodo: str | None = None,
    ) -> list[str]:
        key = f"analytics:escuelas:{modalidad}:{periodo}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return cached
        result = await self.repo.distinct_escuelas(modalidad=modalidad, periodo=periodo)
        await analytics_cache.set(key, result)
        return result

    async def periodos(
        self,
        *,
        modalidad: str | None = None,
    ) -> list[PeriodoOption]:
        key = f"analytics:periodos:{modalidad}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [PeriodoOption(**r) for r in cached]
        rows = await self.repo.distinct_periodos(modalidad=modalidad)
        result = [PeriodoOption(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result

    async def cursos(
        self,
        *,
        escuela: str | None = None,
        modalidad: str | None = None,
        periodo: str | None = None,
    ) -> list[str]:
        key = f"analytics:cursos:{modalidad}:{periodo}:{escuela}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return cached
        result = await self.repo.distinct_cursos(
            escuela=escuela,
            modalidad=modalidad,
            periodo=periodo,
        )
        await analytics_cache.set(key, result)
        return result
