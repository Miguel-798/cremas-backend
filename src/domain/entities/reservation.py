"""
Reservation Entity - Domain Layer

Representa un apartado/reserva de cremas para un cliente.
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid


@dataclass
class Reservation:
    """
    Entidad de dominio para una reserva/apartado.
    
    Attributes:
        id: Identificador único UUID
        cream_id: UUID de la crema reservada
        cream_name: Nombre del sabor (denormalizado para histórico)
        quantity_reserved: Cantidad apartada
        reserved_for: Fecha para la cual se apartó
        customer_name: Nombre del cliente (opcional)
        is_active: Si la reserva está activa o ya se entregó/canceló
        created_at: Fecha de creación de la reserva
    """
    
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    cream_id: uuid.UUID = field(default_factory=uuid.uuid4)
    cream_name: str = ""
    quantity_reserved: int = 0
    reserved_for: date = field(default_factory=date.today)
    customer_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validaciones post-construcción."""
        if self.quantity_reserved <= 0:
            raise ValueError("La cantidad reservada debe ser mayor a 0")
        
        if not self.cream_name:
            raise ValueError("El nombre del sabor es requerido")
        
        if self.customer_name:
            self.customer_name = self.customer_name.strip()
    
    def is_expired(self, expiry_days: int = 2) -> bool:
        """Verificar si la reserva ha expirado."""
        from datetime import timedelta
        expiry_date = self.reserved_for + timedelta(days=expiry_days)
        return date.today() > expiry_date
    
    def activate(self) -> None:
        """Activar la reserva."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Desactivar la reserva (entregada o cancelada)."""
        self.is_active = False
    
    def __repr__(self) -> str:
        status = "activa" if self.is_active else "inactiva"
        return f"Reservation(id={self.id}, cream='{self.cream_name}', quantity={self.quantity_reserved}, for={self.reserved_for}, {status})"
