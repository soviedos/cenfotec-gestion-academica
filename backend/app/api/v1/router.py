from fastapi import APIRouter

from app.api.v1 import analytics, documentos, evaluaciones, qualitative

api_router = APIRouter()

api_router.include_router(evaluaciones.router, prefix="/evaluaciones", tags=["evaluaciones"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(qualitative.router, prefix="/qualitative", tags=["qualitative"])
