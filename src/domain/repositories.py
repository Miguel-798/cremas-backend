"""
Repository Interfaces - Domain Layer

Define las abstracciones para el acceso a datos.
Estas interfaces son implementadas en la capa de infraestructura.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .entities.cream import Cream
from .entities.sale import Sale
from .entities.reservation import Reservation


class CreamRepository(ABC):
    """Interfaz abstracta para repositorio de cremas."""
    
    @abstractmethod
    async def get_all(self) -> List[Cream]:
        """Obtener todas las cremas."""
        pass
    
    @abstractmethod
    async def get_by_id(self, cream_id: UUID) -> Optional[Cream]:
        """Obtener crema por ID."""
        pass
    
    @abstractmethod
    async def get_by_flavor_name(self, flavor_name: str) -> Optional[Cream]:
        """Obtener crema por nombre de sabor."""
        pass
    
    @abstractmethod
    async def create(self, cream: Cream) -> Cream:
        """Crear una nueva crema."""
        pass
    
    @abstractmethod
    async def update(self, cream: Cream) -> Cream:
        """Actualizar una crema existente."""
        pass
    
    @abstractmethod
    async def delete(self, cream_id: UUID) -> bool:
        """Eliminar una crema."""
        pass
    
    @abstractmethod
    async def get_low_stock(self, threshold: int = 3) -> List[Cream]:
        """Obtener cremas con stock bajo."""
        pass


class SaleRepository(ABC):
    """Interfaz abstracta para repositorio de ventas."""
    
    @abstractmethod
    async def get_by_cream_id(self, cream_id: UUID) -> List[Sale]:
        """Obtener todas las ventas de una crema."""
        pass
    
    @abstractmethod
    async def create(self, sale: Sale) -> Sale:
        """Crear una nueva venta."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Sale]:
        """Obtener todas las ventas."""
        pass


class ReservationRepository(ABC):
    """Interfaz abstracta para repositorio de reservas."""
    
    @abstractmethod
    async def get_by_cream_id(self, cream_id: UUID) -> List[Reservation]:
        """Obtener todas las reservas de una crema."""
        pass
    
    @abstractmethod
    async def get_active_by_cream_id(self, cream_id: UUID) -> List[Reservation]:
        """Obtener reservas activas de una crema."""
        pass
    
    @abstractmethod
    async def get_active(self) -> List[Reservation]:
        """Obtener todas las reservas activas."""
        pass
    
    @abstractmethod
    async def create(self, reservation: Reservation) -> Reservation:
        """Crear una nueva reserva."""
        pass
    
    @abstractmethod
    async def update(self, reservation: Reservation) -> Reservation:
        """Actualizar una reserva."""
        pass
    
    @abstractmethod
    async def delete(self, reservation_id: UUID) -> bool:
        """Eliminar una reserva."""
        pass
