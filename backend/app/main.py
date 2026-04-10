from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.deps import DbSession
from app.api.rate_limit import query_rate_limiter
from app.api.v1.router import api_router
from app.core.cache import analytics_cache
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.domain.exceptions import (
    DomainError,
    DuplicateError,
    GeminiError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiUnavailableError,
    NotFoundError,
    ValidationError,
)

logger = get_logger(__name__)


# ── Security headers middleware (pure ASGI — no background-task issue) ───
class SecurityHeadersMiddleware:
    """Inject standard security headers into every response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                extra = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                ]
                if not settings.is_development:
                    extra.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
                    extra.append(
                        (
                            b"content-security-policy",
                            b"default-src 'none'; frame-ancestors 'none'",
                        )
                    )
                message["headers"] = list(message.get("headers", [])) + extra
            await send(message)

        await self.app(scope, receive, send_with_headers)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.environment
    )
    yield
    # Graceful shutdown: close Redis connections
    await analytics_cache.close()
    await query_rate_limiter.close()
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

    # --- Middleware (order matters: last added = first executed) ---
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    # --- Exception handlers ---
    @application.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @application.exception_handler(DuplicateError)
    async def duplicate_handler(_request: Request, exc: DuplicateError):
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @application.exception_handler(ValidationError)
    async def validation_handler(_request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.detail})

    @application.exception_handler(GeminiUnavailableError)
    async def gemini_unavailable_handler(_request: Request, exc: GeminiUnavailableError):
        return JSONResponse(status_code=503, content={"detail": exc.detail})

    @application.exception_handler(GeminiTimeoutError)
    async def gemini_timeout_handler(_request: Request, exc: GeminiTimeoutError):
        return JSONResponse(status_code=504, content={"detail": exc.detail})

    @application.exception_handler(GeminiRateLimitError)
    async def gemini_rate_limit_handler(_request: Request, exc: GeminiRateLimitError):
        return JSONResponse(
            status_code=503,
            content={"detail": exc.detail},
            headers={"Retry-After": "30"},
        )

    @application.exception_handler(GeminiError)
    async def gemini_error_handler(_request: Request, exc: GeminiError):
        return JSONResponse(status_code=502, content={"detail": exc.detail})

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
