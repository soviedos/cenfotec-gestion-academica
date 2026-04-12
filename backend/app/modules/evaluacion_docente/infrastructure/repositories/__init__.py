"""Module repositories."""
from app.modules.evaluacion_docente.infrastructure.repositories.alerta_repo import AlertaRepository
from app.modules.evaluacion_docente.infrastructure.repositories.analytics_repo import (
    AnalyticsRepository,
)
from app.modules.evaluacion_docente.infrastructure.repositories.documento import DocumentoRepository
from app.modules.evaluacion_docente.infrastructure.repositories.duplicado_repo import (
    DuplicadoRepository,
)
from app.modules.evaluacion_docente.infrastructure.repositories.evaluacion import (
    EvaluacionRepository,
)

__all__ = [
    "AlertaRepository",
    "AnalyticsRepository",
    "DocumentoRepository",
    "DuplicadoRepository",
    "EvaluacionRepository",
]
