"""Analytics service — thin business layer for BI dashboard queries."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import analytics_cache
from app.domain.schemas.analytics import (
    DimensionPromedio,
    DocentePromedio,
    PeriodoMetrica,
    RankingDocente,
    ResumenGeneral,
)
from app.infrastructure.repositories.analytics_repo import AnalyticsRepository


class AnalyticsService:
    """Delegates to :class:`AnalyticsRepository` and maps results to schemas.

    Results are cached in-memory for 5 minutes to reduce DB load on
    repeated dashboard visits.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AnalyticsRepository(db)

    async def resumen(
        self, *, periodo: str | None = None, modalidad: str | None = None
    ) -> ResumenGeneral:
        key = f"analytics:resumen:{modalidad}:{periodo}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return ResumenGeneral(**cached)
        data = await self.repo.resumen_global(periodo=periodo, modalidad=modalidad)
        result = ResumenGeneral(**data)
        await analytics_cache.set(key, result.model_dump())
        return result

    async def promedios_docentes(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DocentePromedio]:
        key = f"analytics:docentes:{modalidad}:{periodo}:{limit}:{offset}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [DocentePromedio(**r) for r in cached]
        rows = await self.repo.promedios_por_docente(
            periodo=periodo, modalidad=modalidad, limit=limit, offset=offset
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
    ) -> list[DimensionPromedio]:
        key = f"analytics:dimensiones:{modalidad}:{periodo}:{docente}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [DimensionPromedio(**r) for r in cached]
        rows = await self.repo.promedios_por_dimension(
            periodo=periodo, docente=docente, modalidad=modalidad
        )
        result = [DimensionPromedio(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result

    async def evolucion(
        self,
        *,
        docente: str | None = None,
        modalidad: str | None = None,
    ) -> list[PeriodoMetrica]:
        key = f"analytics:evolucion:{modalidad}:{docente}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [PeriodoMetrica(**r) for r in cached]
        rows = await self.repo.evolucion_periodos(docente=docente, modalidad=modalidad)
        result = [PeriodoMetrica(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result

    async def ranking(
        self,
        *,
        periodo: str | None = None,
        modalidad: str | None = None,
        limit: int = 10,
    ) -> list[RankingDocente]:
        key = f"analytics:ranking:{modalidad}:{periodo}:{limit}"
        cached = await analytics_cache.get(key)
        if cached is not None:
            return [RankingDocente(**r) for r in cached]
        rows = await self.repo.ranking_docentes(periodo=periodo, modalidad=modalidad, limit=limit)
        result = [RankingDocente(**r) for r in rows]
        await analytics_cache.set(key, [r.model_dump() for r in result])
        return result
