"""
Reservation Service - Application Layer

Servicio para gestionar las reservas/apartados de cremas.
"""
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from src.domain import Reservation, Cream, ReservationRepository, CreamRepository
from src.infrastructure.config import settings
from src.infrastructure.cache import (
    get_cache,
    CacheKeys,
    CACHE_TTL,
    invalidate_cache,
)
from src.infrastructure.logging import get_logger

log = get_logger(__name__)


class ReservationService:
    """Servicio para gestionar las reservas de cremas."""
    
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        cream_repo: CreamRepository,
    ):
        self.reservation_repo = reservation_repo
        self.cream_repo = cream_repo
        self.expiry_days = settings.reservation_expiry_days
    
    # ============================================
    # Reservation Operations
    # ============================================
    
    async def create_reservation(
        self,
        cream_id: UUID,
        quantity_reserved: int,
        reserved_for: date,
        customer_name: Optional[str] = None,
    ) -> Reservation:
        """
        Crear una nueva reserva.
        
        Rules:
        - La crema debe existir
        - La cantidad debe ser > 0
        - La fecha debe ser hoy o futura
        """
        cream = await self.cream_repo.get_by_id(cream_id)
        if not cream:
            raise ValueError(f"Crema no encontrada: {cream_id}")
        
        if quantity_reserved <= 0:
            raise ValueError("La cantidad a reservar debe ser mayor a 0")
        
        if reserved_for < date.today():
            raise ValueError("La fecha de reserva no puede ser anterior a hoy")
        
        # Verificar stock disponible
        if quantity_reserved > cream.quantity:
            raise ValueError(
                f"Stock insuficiente. Disponible: {cream.quantity}, "
                f"solicitado: {quantity_reserved}"
            )
        
        # Crear reserva
        reservation = Reservation(
            cream_id=cream_id,
            cream_name=cream.flavor_name,
            quantity_reserved=quantity_reserved,
            reserved_for=reserved_for,
            customer_name=customer_name,
            is_active=True,
        )
        
        result = await self.reservation_repo.create(reservation)
        
        # Invalidate cache
        invalidate_cache(CacheKeys.active_reservations())
        log.debug("cache.invalidated", keys=["active_reservations"])
        
        return result
    
    async def activate_reservation(
        self,
        cream_id: UUID,
        quantity_reserved: int,
        reserved_for: date,
        customer_name: Optional[str] = None,
    ) -> Reservation:
        """
        Reactivar una reserva existente o crear una nueva.
        
        Rules:
        - Si existe una reserva inactiva para esa crema, se reactiva
        - Si no existe, se crea una nueva
        - La奶油 debe existir y tener stock
        """
        cream = await self.cream_repo.get_by_id(cream_id)
        if not cream:
            raise ValueError(f"Crema no encontrada: {cream_id}")
        
        # Buscar reserva existente inactiva para esta crema
        existing_reservations = await self.reservation_repo.get_by_cream_id(cream_id)
        inactive = [r for r in existing_reservations if not r.is_active]
        
        if inactive:
            # Reactivar la más reciente
            reservation = inactive[0]
            reservation.activate()
            reservation.quantity_reserved = quantity_reserved
            reservation.reserved_for = reserved_for
            reservation.customer_name = customer_name
            result = await self.reservation_repo.update(reservation)
            
            # Invalidate cache
            invalidate_cache(CacheKeys.active_reservations())
            log.debug("cache.invalidated", keys=["active_reservations"])
            
            return result
        
        # Crear nueva si no hay inactivas
        return await self.create_reservation(
            cream_id=cream_id,
            quantity_reserved=quantity_reserved,
            reserved_for=reserved_for,
            customer_name=customer_name,
        )
    
    async def cancel_reservation(self, reservation_id: UUID) -> bool:
        """Cancelar una reserva (marcar como inactiva)."""
        reservations = await self.reservation_repo.get_active()
        for res in reservations:
            if res.id == reservation_id:
                res.deactivate()
                await self.reservation_repo.update(res)
                
                # Invalidate cache
                invalidate_cache(CacheKeys.active_reservations())
                log.debug("cache.invalidated", keys=["active_reservations"])
                
                return True
        return False
    
    async def deliver_reservation(self, reservation_id: UUID) -> bool:
        """
        Entregar una reserva.
        
        Esto descuenta el stock y marca la reserva como inactiva.
        """
        reservations = await self.reservation_repo.get_active()
        reservation = None
        for res in reservations:
            if res.id == reservation_id:
                reservation = res
                break
        
        if not reservation:
            raise ValueError(f"Reserva no encontrada o ya entregada: {reservation_id}")
        
        # Descontar stock
        cream = await self.cream_repo.get_by_id(reservation.cream_id)
        if cream:
            cream.remove_stock(reservation.quantity_reserved)
            await self.cream_repo.update(cream)
        
        # Marcar como entregada
        reservation.deactivate()
        await self.reservation_repo.update(reservation)
        
        # Invalidate cache (both reservation and cream caches)
        invalidate_cache(
            CacheKeys.active_reservations(),
            CacheKeys.cream_by_id(str(reservation.cream_id)),
            CacheKeys.low_stock(),
        )
        log.debug("cache.invalidated", keys=["active_reservations", "cream_by_id", "low_stock"])
        
        return True
    
    async def get_active_reservations(self) -> List[Reservation]:
        """Obtener todas las reservas activas (cached)."""
        cache = get_cache()
        cached = await cache.get(CacheKeys.active_reservations())
        if cached is not None:
            return cached
        reservations = await self.reservation_repo.get_active()
        await cache.set(
            CacheKeys.active_reservations(),
            reservations,
            ttl=CACHE_TTL["reservations"],
        )
        return reservations
    
    async def get_reservations_by_cream(self, cream_id: UUID) -> List[Reservation]:
        """Obtener todas las reservas de una crema."""
        return await self.reservation_repo.get_by_cream_id(cream_id)
    
    async def get_active_reservations_by_cream(self, cream_id: UUID) -> List[Reservation]:
        """Obtener reservas activas de una crema."""
        return await self.reservation_repo.get_active_by_cream_id(cream_id)
    
    # ============================================
    # Expiry Operations
    # ============================================
    
    async def get_expired_reservations(self) -> List[Reservation]:
        """Obtener reservas que han expirado."""
        all_active = await self.reservation_repo.get_active()
        expired = []
        
        for res in all_active:
            if res.is_expired(self.expiry_days):
                expired.append(res)
        
        return expired
    
    async def expire_reservations(self) -> int:
        """
        Marcar reservas expiradas como inactivas.
        
        Returns:
            Número de reservas expiradas
        """
        expired = await self.get_expired_reservations()
        
        for res in expired:
            res.deactivate()
            await self.reservation_repo.update(res)
        
        return len(expired)
