"""
API Layer - Routes

Exporta los routers de la API.
"""
from .inventory import router as inventory_router, sales_router

__all__ = ["inventory_router", "sales_router"]
