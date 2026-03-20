"""
Main Application - API Layer

Punto de entrada de la aplicación FastAPI.
"""
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.infrastructure.database import init_db
from src.infrastructure.database.base import engine
from src.infrastructure.config import settings
from src.infrastructure.logging import configure_logging, get_logger, bind_request_context
from src.infrastructure.cache import get_cache
from src.api.routes import inventory_router, sales_router


# ============================================
# Configure logging on module load
# ============================================

configure_logging()
log = get_logger(__name__)


# ============================================
# Rate Limiter Configuration
# ============================================

def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on user or IP."""
    # If user is authenticated, use their ID for rate limiting
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.id}"
    # Otherwise use IP address
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["100/minute"],  # Default: 100 requests per minute
)


# ============================================
# Lifecycle Manager
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager para la aplicación.
    
    Ejecuta código al iniciar y al cerrar.
    """
    # Startup
    log.info("app.starting", app_name=settings.app_name, version=settings.app_version, env=settings.env)
    
    try:
        await init_db()
        log.info("app.db_initialized")
    except Exception as e:
        log.warning("app.db_init_failed", error=str(e))
    
    yield
    
    # Shutdown
    log.info("app.shutdown")


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para gestionar el inventario de cremas",
    lifespan=lifespan,
)


# ============================================
# Request ID Middleware
# ============================================

@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    Middleware that adds a unique request ID to each request.
    
    - Generates a UUID if X-Request-ID header is not present
    - Binds request context to structlog for all log entries
    - Adds X-Request-ID to response headers
    """
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    # Bind context for all logs in this request
    bind_request_context(
        request_id=request_id,
        path=str(request.url.path),
    )
    
    log.info("request.started", method=request.method, path=str(request.url.path))
    
    response = await call_next(request)
    
    # Always include request ID in response
    response.headers["X-Request-ID"] = request_id
    log.info("request.completed", status_code=response.status_code)
    
    return response


# ============================================
# Global Exception Handler
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unhandled errors.
    
    Returns HTTP 500 with a generic error message.
    Request ID is included for log correlation.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    log.error(
        "request.unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - configured from config.yaml
# In development: allow localhost:3000 with credentials
# In production: allow configured production origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Routes
# ============================================

app.include_router(inventory_router)
app.include_router(sales_router)


# ============================================
# Health Check (no rate limit)
# ============================================

@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Endpoint de verificación de salud con estado de base de datos.
    
    Verifica la conectividad a PostgreSQL ejecutando una query simple.
    """
    db_status = "unavailable"
    db_error = None
    
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.env,
        "database": {
            "status": db_status,
            "error": db_error,
        },
    }


@app.get("/", include_in_schema=False)
async def root():
    """Endpoint raíz."""
    return {
        "message": "Cremas Inventory API",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================
# Debug Endpoints (development only)
# ============================================

@app.get("/debug/cache", include_in_schema=False)
async def debug_cache():
    """
    Debug endpoint for cache statistics.
    
    DEVELOPMENT ONLY - should be disabled in production.
    """
    if settings.is_production:
        return JSONResponse(
            status_code=403,
            content={"error": "Disabled in production"},
        )
    
    cache = get_cache()
    return {
        "cache": cache.stats(),
        "cache_enabled": settings.cache_enabled,
    }


@app.post("/debug/cache/clear", include_in_schema=False)
async def debug_cache_clear():
    """
    Clear the cache (development only).
    
    DEVELOPMENT ONLY - should be disabled in production.
    """
    if settings.is_production:
        return JSONResponse(
            status_code=403,
            content={"error": "Disabled in production"},
        )
    
    cache = get_cache()
    await cache.clear()
    return {"message": "Cache cleared"}
