"""Executive dashboard API endpoint."""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.modules.evaluacion_docente.application.services.dashboard_service import DashboardService
from app.modules.evaluacion_docente.domain.schemas.dashboard import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: DbSession,
    modalidad: str | None = Query(None, description="Filtrar por modalidad"),
) -> DashboardSummary:
    """Return aggregated executive dashboard data."""
    svc = DashboardService(db)
    return await svc.summary(modalidad=modalidad)
