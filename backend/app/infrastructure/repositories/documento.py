"""Documento repository — persistence operations for uploaded PDFs."""

from sqlalchemy import select

from app.domain.entities.documento import Documento
from app.infrastructure.repositories.base import BaseRepository


class DocumentoRepository(BaseRepository[Documento]):
    model = Documento

    async def get_by_hash(self, hash_sha256: str) -> Documento | None:
        stmt = select(Documento).where(Documento.hash_sha256 == hash_sha256)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
