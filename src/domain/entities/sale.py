"""
Sale Entity - Domain Layer

Representa una venta de cremas.
"""
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Sale:
    """
    Entidad de dominio para una venta.
    
    Attributes:
        id: Identificador único UUID
        cream_id: UUID de la crema vendida
        cream_name: Nombre del sabor (denormalizado para histórico)
        quantity_sold: Cantidad de cremas vendidas
        sold_at: Fecha y hora de la venta
    """
    
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    cream_id: uuid.UUID = field(default_factory=uuid.uuid4)
    cream_name: str = ""
    quantity_sold: int = 0
    sold_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validaciones post-construcción."""
        if self.quantity_sold <= 0:
            raise ValueError("La cantidad vendida debe ser mayor a 0")
        
        if not self.cream_name:
            raise ValueError("El nombre del sabor es requerido")
    
    def __repr__(self) -> str:
        return f"Sale(id={self.id}, cream='{self.cream_name}', quantity={self.quantity_sold}, sold_at={self.sold_at})"
