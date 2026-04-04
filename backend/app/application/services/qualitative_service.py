"""Qualitative analysis service — orchestrates repo queries and schema mapping."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.qualitative import (
    ComentarioAnalisisRead,
    NubePalabras,
    PalabraFrecuencia,
    ResumenCualitativo,
    SentimientoDistribucion,
    TemaDistribucion,
    TipoConteo,
)
from app.infrastructure.repositories.qualitative_repo import QualitativeRepository


class QualitativeService:
    """Thin service: delegates to QualitativeRepository, maps to schemas."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = QualitativeRepository(db)

    async def filtros_disponibles(self) -> dict:
        """Return available filter option values."""
        return await self.repo.filtros_disponibles()

    async def resumen(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
    ) -> ResumenCualitativo:
        data = await self.repo.resumen(
            periodo=periodo, docente=docente,
            asignatura=asignatura, escuela=escuela,
        )
        return ResumenCualitativo(
            total_comentarios=data["total_comentarios"],
            por_tipo=[TipoConteo(**t) for t in data["por_tipo"]],
            por_sentimiento=[SentimientoDistribucion(**s) for s in data["por_sentimiento"]],
            temas_top=[TemaDistribucion(**t) for t in data["temas_top"]],
            sentimiento_promedio=data["sentimiento_promedio"],
        )

    async def listar_comentarios(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        tipo: str | None = None,
        tema: str | None = None,
        sentimiento: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ComentarioAnalisisRead], int]:
        """Return paginated comment list with total count."""
        items = await self.repo.listar_comentarios(
            periodo=periodo,
            docente=docente,
            asignatura=asignatura,
            escuela=escuela,
            tipo=tipo,
            tema=tema,
            sentimiento=sentimiento,
            limit=limit,
            offset=offset,
        )
        total = await self.repo.contar_comentarios(
            periodo=periodo,
            docente=docente,
            asignatura=asignatura,
            escuela=escuela,
            tipo=tipo,
            tema=tema,
            sentimiento=sentimiento,
        )
        return [ComentarioAnalisisRead.model_validate(i) for i in items], total

    async def distribucion_temas(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        tipo: str | None = None,
    ) -> list[TemaDistribucion]:
        rows = await self.repo.distribucion_temas(
            periodo=periodo, docente=docente, asignatura=asignatura, escuela=escuela, tipo=tipo
        )
        return [TemaDistribucion(**r) for r in rows]

    async def distribucion_sentimiento(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        tipo: str | None = None,
        tema: str | None = None,
    ) -> list[SentimientoDistribucion]:
        rows = await self.repo.distribucion_sentimiento(
            periodo=periodo, docente=docente,
            asignatura=asignatura, escuela=escuela,
            tipo=tipo, tema=tema,
        )
        return [SentimientoDistribucion(**r) for r in rows]

    async def nube_palabras(
        self,
        *,
        periodo: str | None = None,
        docente: str | None = None,
        asignatura: str | None = None,
        escuela: str | None = None,
        tipo: str | None = None,
    ) -> NubePalabras:
        palabras = await self.repo.nube_palabras(
            periodo=periodo, docente=docente, asignatura=asignatura, escuela=escuela, tipo=tipo
        )
        return NubePalabras(
            tipo=tipo or "all",
            palabras=[PalabraFrecuencia(**p) for p in palabras],
        )
