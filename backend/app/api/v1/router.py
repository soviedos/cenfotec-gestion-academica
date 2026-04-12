from fastapi import APIRouter

from app.modules.auth.api import routes as auth_routes
from app.modules.evaluacion_docente.api import (
    alertas,
    analytics,
    config_routes,
    dashboard,
    documentos,
    evaluaciones,
    qualitative,
    query,
)

api_router = APIRouter()

# Auth
api_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])

# Evaluación docente
api_router.include_router(evaluaciones.router, prefix="/evaluaciones", tags=["evaluaciones"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(qualitative.router, prefix="/qualitative", tags=["qualitative"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(alertas.router, prefix="/alertas", tags=["alertas"])
api_router.include_router(config_routes.router, prefix="/config", tags=["config"])
