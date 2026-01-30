"""
Main FastAPI application for Disease-Relater API.

Entry point for the REST API server providing disease comorbidity data,
network analysis, and 3D visualization coordinates.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from api.config import get_settings
from api.middleware.error_handlers import setup_exception_handlers
from api.routes import calculate, chapters, diseases, health, network

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events.

    Handles:
    - Startup: Load configuration, initialize connections
    - Shutdown: Cleanup resources, close connections
    """
    # Startup
    logger.info("Starting Disease-Relater API...")
    settings = get_settings()
    logger.info(f"App: {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # TODO: Initialize database connection pool here

    yield

    # Shutdown
    logger.info("Shutting down Disease-Relater API...")
    # TODO: Cleanup resources here


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
        """,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(diseases.router, prefix="/api", tags=["diseases"])
    app.include_router(network.router, prefix="/api", tags=["network"])
    app.include_router(chapters.router, prefix="/api", tags=["chapters"])
    app.include_router(calculate.router, prefix="/api", tags=["risk-calculation"])

    # Root endpoint
    @app.get("/")
    async def root():
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
    async def api_info():
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
