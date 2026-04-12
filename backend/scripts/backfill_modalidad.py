"""Backfill modalidad, año, periodo_orden for existing evaluaciones.

Reads the ``periodo`` column of every evaluation and applies
``parse_periodo()`` to derive the correct ``modalidad``, ``año``,
and ``periodo_orden`` values.

Run once:
    cd backend && .venv/bin/python _backfill_modalidad.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion
from app.modules.evaluacion_docente.domain.periodo import parse_periodo
from app.shared.infrastructure.database.session import async_session_factory


async def backfill() -> None:
    async with async_session_factory() as db:
        db: AsyncSession

        rows = (await db.execute(select(Evaluacion.id, Evaluacion.periodo))).all()
        print(f"Found {len(rows)} evaluaciones to backfill")

        updated = 0
        for eval_id, periodo in rows:
            info = parse_periodo(periodo)
            await db.execute(
                update(Evaluacion)
                .where(Evaluacion.id == eval_id)
                .values(
                    modalidad=info.modalidad.value,
                    año=info.año,
                    periodo_orden=info.periodo_orden,
                )
            )
            updated += 1

        await db.commit()
        print(f"Updated {updated} evaluaciones")

        # Verify
        stmt = select(Evaluacion.modalidad, Evaluacion.periodo).limit(10)
        sample = (await db.execute(stmt)).all()
        print("\nSample after backfill:")
        for r in sample:
            print(f"  modalidad={r[0]!r}, periodo={r[1]!r}")

        from sqlalchemy import func

        dist = (
            await db.execute(
                select(Evaluacion.modalidad, func.count(Evaluacion.id)).group_by(
                    Evaluacion.modalidad
                )
            )
        ).all()
        print("\nDistribution:")
        for mod, cnt in dist:
            print(f"  {mod}: {cnt}")


if __name__ == "__main__":
    asyncio.run(backfill())
