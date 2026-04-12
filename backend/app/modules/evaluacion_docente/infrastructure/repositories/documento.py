"""Documento repository — persistence operations for uploaded PDFs."""

from sqlalchemy import func, select

from app.modules.evaluacion_docente.domain.entities.documento import Documento
from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion
from app.shared.infrastructure.repositories.base import BaseRepository

SORT_FIELDS = {
    "created_at": Documento.created_at,
    "updated_at": Documento.updated_at,
    "nombre_archivo": Documento.nombre_archivo,
    "estado": Documento.estado,
    "tamano_bytes": Documento.tamano_bytes,
}


class DocumentoRepository(BaseRepository[Documento]):
    model = Documento

    async def get_by_hash(self, hash_sha256: str) -> Documento | None:
        stmt = select(Documento).where(Documento.hash_sha256 == hash_sha256)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, documento: Documento) -> None:
        await self.session.delete(documento)
        await self.session.flush()

    async def distinct_periodos(self) -> list[str]:
        """Return sorted distinct periodos from evaluaciones."""
        stmt = select(func.distinct(Evaluacion.periodo)).order_by(Evaluacion.periodo)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def list_filtered(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        estado: str | None = None,
        docente: str | None = None,
        periodo: str | None = None,
        nombre_archivo: str | None = None,
        posible_duplicado: bool | None = None,
    ) -> list[Documento]:
        stmt = select(Documento)
        stmt = self._apply_filters(
            stmt,
            estado=estado,
            docente=docente,
            periodo=periodo,
            nombre_archivo=nombre_archivo,
            posible_duplicado=posible_duplicado,
        )
        column = SORT_FIELDS.get(sort_by, Documento.created_at)
        stmt = stmt.order_by(column.desc() if sort_order == "desc" else column.asc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        estado: str | None = None,
        docente: str | None = None,
        periodo: str | None = None,
        nombre_archivo: str | None = None,
        posible_duplicado: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Documento)
        stmt = self._apply_filters(
            stmt,
            estado=estado,
            docente=docente,
            periodo=periodo,
            nombre_archivo=nombre_archivo,
            posible_duplicado=posible_duplicado,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def _apply_filters(
        stmt,
        *,
        estado: str | None,
        docente: str | None,
        periodo: str | None,
        nombre_archivo: str | None,
        posible_duplicado: bool | None = None,
    ):
        if estado:
            stmt = stmt.where(Documento.estado == estado)
        if nombre_archivo:
            stmt = stmt.where(Documento.nombre_archivo.ilike(f"%{nombre_archivo}%"))
        if posible_duplicado is not None:
            stmt = stmt.where(Documento.posible_duplicado == posible_duplicado)
        if docente or periodo:
            conditions = [Evaluacion.documento_id == Documento.id]
            if docente:
                conditions.append(Evaluacion.docente_nombre.ilike(f"%{docente}%"))
            if periodo:
                conditions.append(Evaluacion.periodo == periodo)
            stmt = stmt.where(select(Evaluacion.documento_id).where(*conditions).exists())
        return stmt
