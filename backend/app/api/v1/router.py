from fastapi import APIRouter

from app.api.v1 import documentos, evaluaciones

api_router = APIRouter()

api_router.include_router(evaluaciones.router, prefix="/evaluaciones", tags=["evaluaciones"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
