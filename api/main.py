"""
Main FastAPI application for Disease-Relater API.

Entry point for the REST API server providing disease comorbidity data,
network analysis, and 3D visualization coordinates.
"""

import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.config import get_settings
from api.middleware.error_handlers import setup_exception_handlers
from api.middleware.request_logging import RequestLoggingMiddleware
from api.rate_limit import limiter, get_rate_limit_string, custom_rate_limit_handler
from api.routes import calculate, chapters, diseases, health, network

# OpenAPI tags metadata for organized API documentation
tags_metadata = [
    {
        "name": "health",
        "description": (
            "Health check and monitoring endpoints for service status "
            "and Kubernetes probes"
        ),
    },
    {
        "name": "diseases",
        "description": (
            "Disease data operations including listing, search, details, "
            "and related diseases"
        ),
    },
    {
        "name": "network",
        "description": (
            "Network visualization data with 3D coordinates and "
            "comorbidity relationships"
        ),
    },
    {
        "name": "chapters",
        "description": "ICD-10 chapter listings with disease counts and statistics",
    },
    {
        "name": "risk-calculation",
        "description": (
            "Personalized disease risk calculation based on demographics "
            "and existing conditions"
        ),
    },
]

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add rotating file handler for request/error logging (INFO level for request tracking)
os.makedirs("logs", exist_ok=True)
file_handler = RotatingFileHandler("logs/api.log", maxBytes=10_000_000, backupCount=5)
file_handler.setLevel(logging.INFO)  # Log INFO and above to file for request tracking
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events.

    Handles:
    - Startup: Load configuration, initialize Supabase client, verify indexes
    - Shutdown: Cleanup resources, close connections
    """
    from api.dependencies import (
        init_supabase_client,
        close_supabase_client,
        verify_database_indexes,
    )

    # Startup
    logger.info("Starting Disease-Relater API...")
    settings = get_settings()
    logger.info(f"App: {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize Supabase client (connection pooling via httpx)
    try:
        await init_supabase_client()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        # Don't fail startup - allow late initialization for graceful degradation
        logger.warning("API will attempt to connect to database on first request")

    # Optionally verify database indexes
    if settings.verify_indexes_on_startup:
        logger.info("Verifying database indexes...")
        all_exist, missing = await verify_database_indexes()
        if not all_exist:
            logger.warning(
                f"Some database indexes are missing. Query performance may be degraded. "
                f"Missing: {', '.join(missing)}"
            )
    else:
        logger.debug(
            "Index verification disabled. Set VERIFY_INDEXES_ON_STARTUP=true to enable."
        )

    yield

    # Shutdown
    logger.info("Shutting down Disease-Relater API...")
    await close_supabase_client()
    logger.info("Cleanup complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="""
        Disease-Relater API provides access to comorbidity network data
        derived from 8.9 million Austrian hospital patients (1997-2014).
        
        ## Features
        
        - Query diseases by ICD-10 code
        - Find related diseases by odds ratio
        - Get network data for visualization
        - Access 3D disease coordinates
        - Filter by demographics (sex, age)
        
        ## Data Sources
        
        - 1,080 ICD-10 diseases
        - 9,232 aggregated relationships
        - 74,901 stratified relationships
        - 3D embeddings for network visualization
        
        ## Documentation
        
        - Full API documentation: see API_DOCUMENTATION.md
        - OpenAPI schema: /openapi.json (dev mode only)
        - Swagger UI: /docs (dev mode only)
        - ReDoc: /redoc (dev mode only)
        """,
        version=settings.app_version,
        contact={
            "name": "Disease Relater Team",
            "email": "support@disease-relater.example.com",
            "url": "https://github.com/anomalyco/disease-relater/issues",
        },
        license_info={
            "name": "MIT License",
            "identifier": "MIT",
        },
        openapi_tags=tags_metadata,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Add rate limiting middleware with custom 429 handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Add request logging middleware (logs requests with timing info)
    app.add_middleware(RequestLoggingMiddleware)

    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(diseases.router, prefix="/api", tags=["diseases"])
    app.include_router(network.router, prefix="/api", tags=["network"])
    app.include_router(chapters.router, prefix="/api", tags=["chapters"])
    app.include_router(calculate.router, prefix="/api", tags=["risk-calculation"])

    # Root endpoint with rate limiting
    rate_limit = get_rate_limit_string()

    @app.get("/")
    @limiter.limit(rate_limit)
    async def root(request: Request):
        """API root endpoint with basic information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "operational",
            "documentation": "/docs" if settings.debug else None,
            "health": "/api/health",
        }

    # API info endpoint
    @app.get("/api")
    @limiter.limit(rate_limit)
    async def api_info(request: Request):
        """API information and available endpoints."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "endpoints": {
                "health": "/api/health",
                "diseases": "/api/diseases",
                "network": "/api/network",
                "chapters": "/api/chapters",
                "calculate-risk": "/api/calculate-risk",
            },
            "documentation": "/docs" if settings.debug else None,
        }

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    logger.info(f"Starting server on {settings.host}:{settings.port}")

    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
