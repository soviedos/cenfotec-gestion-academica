"""Backfill escuela from course code prefix and clean \\n from nombre.

Run:  .venv/bin/python _backfill_escuelas.py
"""

import asyncio

from sqlalchemy import text

from app.shared.infrastructure.database.session import async_session_factory

# Same mapping as in courses.py parser
PREFIX_ESCUELA: dict[str, str] = {
    "SOFT": "Ingeniería del Software",
    "BISOFT": "Ingeniería del Software",
    "TSOFT": "Ingeniería del Software",
    "PSWE": "Ingeniería del Software",
    "INF": "Tecnologías de Información",
    "TINF": "Tecnologías de Información",
    "BITIC": "Tecnologías de Información",
    "SINF": "Sistemas de Información",
    "SINT": "Sistemas de Información",
    "DIWEB": "Diseño Web",
    "TWEB": "Diseño Web",
    "COMP": "Computación",
    "CIB": "Ciberseguridad",
    "FUN": "Fundamentos",
    "PIA": "Fundamentos",
}


async def main() -> None:
    async with async_session_factory() as session:
        # 1. Clean \n from nombre
        result = await session.execute(
            text(
                "UPDATE evaluacion_cursos"
                " SET nombre = REPLACE(nombre, chr(10), ' ')"
                " WHERE nombre LIKE '%' || chr(10) || '%'"
            )
        )
        print(f"Cleaned \\n from {result.rowcount} course names")

        # 2. Set escuela from code prefix
        total = 0
        for prefix, escuela in PREFIX_ESCUELA.items():
            r = await session.execute(
                text(
                    "UPDATE evaluacion_cursos SET escuela = :escuela "
                    "WHERE codigo LIKE :pattern AND (escuela IS NULL OR escuela = 'DESCONOCIDA')"
                ),
                {"escuela": escuela, "pattern": f"{prefix}-%"},
            )
            if r.rowcount:
                print(f"  {prefix}-* → {escuela}: {r.rowcount} rows")
                total += r.rowcount

        print(f"Updated escuela for {total} rows total")

        # 3. Report remaining unknowns
        r = await session.execute(
            text(
                "SELECT COUNT(*) FROM evaluacion_cursos"
                " WHERE escuela IS NULL OR escuela = 'DESCONOCIDA'"
            )
        )
        remaining = r.scalar()
        if remaining:
            print(f"⚠ {remaining} rows still have unknown escuela")

        await session.commit()
        print("✓ Backfill complete")


if __name__ == "__main__":
    asyncio.run(main())
