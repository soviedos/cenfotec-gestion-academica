"""Shared entity barrel — re-exports Base.

Module entities are registered via Alembic's env.py, which imports
each module's entity barrel directly.  This avoids circular imports
(module entities inherit from Base defined here in shared).
"""

from app.shared.domain.entities.base import Base  # noqa: F401
