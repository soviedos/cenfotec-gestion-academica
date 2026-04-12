"""seed admin user soviedo@ucenfotec.ac.cr

Revision ID: 0015
Revises: 0014
Create Date: 2026-04-12 19:01:00.000000
"""

from collections.abc import Sequence

import bcrypt
import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ADMIN_EMAIL = "soviedo@ucenfotec.ac.cr"
ADMIN_PASSWORD = "Admin"


def upgrade() -> None:
    password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()

    op.execute(
        sa.text(
            """
            INSERT INTO users (
                id, email, nombre, google_sub,
                role, password_hash, activo,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :email, :nombre,
                :google_sub, :role, :password_hash,
                true, now(), now()
            )
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role
            """
        ).bindparams(
            email=ADMIN_EMAIL,
            nombre="Sergio Oviedo Seas",
            google_sub=f"dev-{ADMIN_EMAIL}",
            role="admin",
            password_hash=password_hash,
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM users WHERE email = :email").bindparams(email=ADMIN_EMAIL))
