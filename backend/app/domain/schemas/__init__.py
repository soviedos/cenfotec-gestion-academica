from app.domain.schemas.common import (
    BaseSchema,
    ErrorResponse,
    HealthResponse,
    PaginatedItems,
    PaginatedResponse,
)
from app.domain.schemas.documento import (
                                       DocumentoCreate,
                                       DocumentoList,
                                       DocumentoRead,
                                       DocumentoUploadResponse,
)
from app.domain.schemas.evaluacion import EvaluacionList, EvaluacionRead

__all__ = [
    "BaseSchema",
    "DocumentoCreate",
    "DocumentoList",
    "DocumentoRead",
    "DocumentoUploadResponse",
    "ErrorResponse",
    "EvaluacionList",
    "EvaluacionRead",
    "HealthResponse",
    "PaginatedItems",
    "PaginatedResponse",
]
