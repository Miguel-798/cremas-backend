"""
Inventory Service - Application Layer

Servicio para gestionar el inventario de cremas.
"""
from typing import List, Optional
from uuid import UUID

from src.domain import Cream, Sale, CreamRepository, SaleRepository
from src.infrastructure.config import settings
from src.infrastructure.cache import (
    get_cache,
    CacheKeys,
    CACHE_TTL,
    invalidate_cache,
)
from src.infrastructure.logging import get_logger

log = get_logger(__name__)


class InventoryService:
    """Servicio para gestionar el inventario de cremas."""
    
    def __init__(
        self,
        cream_repo: CreamRepository,
        sale_repo: SaleRepository,
    ):
        self.cream_repo = cream_repo
        self.sale_repo = sale_repo
        self.low_stock_threshold = settings.low_stock_threshold
    
    # ============================================
    # Cream Operations
    # ============================================
    
    async def get_all_creams(self) -> List[Cream]:
        """Obtener todas las cremas (cached)."""
        cache = get_cache()
        cached = await cache.get(CacheKeys.creams())
        if cached is not None:
            return cached
        creams = await self.cream_repo.get_all()
        await cache.set(CacheKeys.creams(), creams, ttl=CACHE_TTL["creams"])
        return creams
    
    async def get_cream_by_id(self, cream_id: UUID) -> Optional[Cream]:
        """Obtener una crema por ID (cached)."""
        cache = get_cache()
        cached = await cache.get(CacheKeys.cream_by_id(str(cream_id)))
        if cached is not None:
            return cached
        cream = await self.cream_repo.get_by_id(cream_id)
        if cream is not None:
            await cache.set(
                CacheKeys.cream_by_id(str(cream_id)),
                cream,
                ttl=CACHE_TTL["cream_by_id"],
            )
        return cream
    
    async def create_cream(self, flavor_name: str, price: float = 0.0, quantity: int = 0) -> Cream:
        """Crear una nueva crema."""
        # Verificar que no exista
        existing = await self.cream_repo.get_by_flavor_name(flavor_name)
        if existing:
            raise ValueError(f"Ya existe una crema con el sabor: {flavor_name}")
        
        cream = Cream(flavor_name=flavor_name, price=price, quantity=quantity)
        result = await self.cream_repo.create(cream)
        
        # Invalidate cache
        invalidate_cache(CacheKeys.creams(), CacheKeys.low_stock())
        log.debug("cache.invalidated", keys=["creams", "low_stock"])
        
        return result
    
    async def update_cream_quantity(self, cream_id: UUID, quantity: int) -> Cream:
        """Actualizar la cantidad de una crema (set completo)."""
        cream = await self.cream_repo.get_by_id(cream_id)
        if not cream:
            raise ValueError(f"Crema no encontrada: {cream_id}")
        
        cream.quantity = quantity
        result = await self.cream_repo.update(cream)
        
        # Invalidate cache
        invalidate_cache(
            CacheKeys.creams(),
            CacheKeys.cream_by_id(str(cream_id)),
            CacheKeys.low_stock(),
        )
        log.debug("cache.invalidated", keys=["creams", "cream_by_id", "low_stock"])
        
        return result
    
    async def update_cream(self, cream_id: UUID, flavor_name: Optional[str] = None, price: Optional[float] = None, quantity: Optional[int] = None) -> Cream:
        """Actualizar crema (parcial - solo campos proporcionados)."""
        cream = await self.cream_repo.get_by_id(cream_id)
        if not cream:
            raise ValueError(f"Crema no encontrada: {cream_id}")
        
        # Update only provided fields
        if flavor_name is not None:
            cream.flavor_name = flavor_name
        if price is not None:
            cream.price = price
        if quantity is not None:
            cream.quantity = quantity
        
        result = await self.cream_repo.update(cream)
        
        # Invalidate cache
        invalidate_cache(
            CacheKeys.creams(),
            CacheKeys.cream_by_id(str(cream_id)),
            CacheKeys.low_stock(),
        )
        log.debug("cache.invalidated", keys=["creams", "cream_by_id", "low_stock"])
        
        return result
    
    async def delete_sale(self, sale_id: UUID) -> bool:
        """Eliminar una venta y restaurar el inventario."""
        # Get the sale first
        sale = await self.sale_repo.get_by_id(sale_id)
        if not sale:
            raise ValueError(f"Venta no encontrada: {sale_id}")
        
        # Restore inventory
        cream = await self.cream_repo.get_by_id(sale.cream_id)
        if cream:
            cream.add_stock(sale.quantity_sold)
            await self.cream_repo.update(cream)
        
        # Delete the sale
        result = await self.sale_repo.delete(sale_id)
        
        # Invalidate cache
        invalidate_cache(
            CacheKeys.creams(),
            CacheKeys.cream_by_id(str(sale.cream_id)),
            CacheKeys.low_stock(),
            CacheKeys.sales(),
            CacheKeys.sales_by_cream(str(sale.cream_id)),
        )
        log.debug("cache.invalidated", keys=["creams", "cream_by_id", "low_stock", "sales"])
        
        return result
    
    async def add_stock(self, cream_id: UUID, amount: int) -> Cream:
        """Agregar stock a una crema."""
        cream = await self.cream_repo.get_by_id(cream_id)
        if not cream:
            raise ValueError(f"Crema no encontrada: {cream_id}")
        
        cream.add_stock(amount)
        result = await self.cream_repo.update(cream)
        
        # Invalidate cache
        invalidate_cache(
            CacheKeys.creams(),
            CacheKeys.cream_by_id(str(cream_id)),
            CacheKeys.low_stock(),
        )
        log.debug("cache.invalidated", keys=["creams", "cream_by_id", "low_stock"])
        
        return result
    
    async def delete_cream(self, cream_id: UUID) -> bool:
        """Eliminar una crema."""
        result = await self.cream_repo.delete(cream_id)
        
        # Invalidate cache
        invalidate_cache(
            CacheKeys.creams(),
            CacheKeys.cream_by_id(str(cream_id)),
            CacheKeys.low_stock(),
        )
        log.debug("cache.invalidated", keys=["creams", "cream_by_id", "low_stock"])
        
        return result
    
    # ============================================
    # Sale Operations
    # ============================================
    
    async def register_sale(
        self, 
        cream_id: UUID, 
        quantity_sold: int, 
        manual_price: Optional[float] = None
    ) -> Sale:
        """
        Registrar una venta.
        
        Este método:
        1. Verifica que haya stock suficiente
        2. Descuenta el stock automáticamente
        3. Crea el registro de venta
        4. Usa el precio manual si se proporciona, si no usa el precio de la crema
        """
        cream = await self.cream_repo.get_by_id(cream_id)
        if not cream:
            raise ValueError(f"Crema no encontrada: {cream_id}")
        
        # Verificar stock disponible (considerando reservas activas)
        from .reservation_service import ReservationService
        # Por ahora solo verificamos stock directo
        if quantity_sold > cream.quantity:
            raise ValueError(
                f"Stock insuficiente. Disponible: {cream.quantity}, "
                f"solicitado: {quantity_sold}"
            )
        
# Descontar stock
        cream.remove_stock(quantity_sold)
        await self.cream_repo.update(cream)
        
        # Use manual price if provided, otherwise use cream's price
        price = manual_price if manual_price is not None else cream.price
        total = price * quantity_sold
        
        # Crear registro de venta
        sale = Sale(
            cream_id=cream_id,
            cream_name=cream.flavor_name,
            quantity_sold=quantity_sold,
            price=price,
        )
        result = await self.sale_repo.create(sale)
        
        # Invalidate cache (stock changed)
        invalidate_cache(
            CacheKeys.creams(),
            CacheKeys.cream_by_id(str(cream_id)),
            CacheKeys.low_stock(),
            CacheKeys.sales(),
            CacheKeys.sales_by_cream(str(cream_id)),
        )
        log.debug("cache.invalidated", keys=["creams", "cream_by_id", "low_stock", "sales"])
        
        return result
    
    async def get_sales_by_cream(self, cream_id: UUID) -> List[Sale]:
        """Obtener historial de ventas de una crema."""
        return await self.sale_repo.get_by_cream_id(cream_id)
    
    async def get_all_sales(self) -> List[Sale]:
        """Obtener todas las ventas."""
        return await self.sale_repo.get_all()
    
    # ============================================
    # Low Stock Operations
    # ============================================
    
    async def get_low_stock_creams(self) -> List[Cream]:
        """Obtener cremas con stock bajo (≤ threshold) (cached)."""
        cache = get_cache()
        cached = await cache.get(CacheKeys.low_stock())
        if cached is not None:
            return cached
        creams = await self.cream_repo.get_low_stock(self.low_stock_threshold)
        await cache.set(CacheKeys.low_stock(), creams, ttl=CACHE_TTL["low_stock"])
        return creams
    
    async def check_low_stock(self, cream: Cream) -> bool:
        """Verificar si una crema tiene stock bajo."""
        return cream.is_low_stock(self.low_stock_threshold)
