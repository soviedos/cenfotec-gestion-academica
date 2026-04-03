from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import DbSession
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.domain.exceptions import DomainError, DuplicateError, NotFoundError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.environment
    )
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    """Application factory."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # --- Middleware ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception handlers ---
    @application.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @application.exception_handler(DuplicateError)
    async def duplicate_handler(_request: Request, exc: DuplicateError):
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @application.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError):
        return JSONResponse(status_code=400, content={"detail": exc.detail})

    # --- Routes ---
    application.include_router(api_router, prefix="/api/v1")

    @application.get("/health")
    async def health_check(db: DbSession):
        """Health check — includes a lightweight DB ping."""
        db_ok = True
        try:
            await db.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
        return {
            "status": "ok" if db_ok else "degraded",
            "version": settings.app_version,
            "environment": settings.environment,
            "database": "connected" if db_ok else "unreachable",
        }

    return application


app = create_app()
