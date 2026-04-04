"""Analytics service — thin business layer for BI dashboard queries."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.analytics import (
    DimensionPromedio,
    DocentePromedio,
    PeriodoMetrica,
    RankingDocente,
    ResumenGeneral,
)
from app.infrastructure.repositories.analytics_repo import AnalyticsRepository


class AnalyticsService:
    """Delegates to :class:`AnalyticsRepository` and maps results to schemas."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AnalyticsRepository(db)

    async def resumen(self, *, periodo: str | None = None) -> ResumenGeneral:
        data = await self.repo.resumen_global(periodo=periodo)
        return ResumenGeneral(**data)

    async def promedios_docentes(
        self,
        *,
        periodo: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DocentePromedio]:
        rows = await self.repo.promedios_por_docente(
            periodo=periodo, limit=limit, offset=offset
        )
        return [DocentePromedio(**r) for r in rows]

    async def dimensiones(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
    ) -> list[DimensionPromedio]:
        rows = await self.repo.promedios_por_dimension(
            periodo=periodo, docente=docente
        )
        return [DimensionPromedio(**r) for r in rows]

    async def evolucion(
        self,
        *,
        docente: str | None = None,
    ) -> list[PeriodoMetrica]:
        rows = await self.repo.evolucion_periodos(docente=docente)
        return [PeriodoMetrica(**r) for r in rows]

    async def ranking(
        self,
        *,
        periodo: str | None = None,
        limit: int = 10,
    ) -> list[RankingDocente]:
        rows = await self.repo.ranking_docentes(periodo=periodo, limit=limit)
        return [RankingDocente(**r) for r in rows]
