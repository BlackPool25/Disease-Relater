"""
API Routes Package

Exports all route modules for easy importing.
Includes all routers: health, diseases, network, chapters, calculate.
"""

from api.routes.health import router as health_router
from api.routes.diseases import router as diseases_router
from api.routes.network import router as network_router
from api.routes.chapters import router as chapters_router
from api.routes.calculate import router as calculate_router

__all__ = [
    "health_router",
    "diseases_router",
    "network_router",
    "chapters_router",
    "calculate_router",
]
