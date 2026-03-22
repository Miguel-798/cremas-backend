"""
Cream Entity - Domain Layer

Representa un sabor de crema en el inventario.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Cream:
    """
    Entidad de dominio para una crema/sabor.
    
    Attributes:
        id: Identificador único UUID
        flavor_name: Nombre del sabor (ej: "Chocolate Blanco")
        price: Precio de la crema (float)
        quantity: Cantidad actual en inventario
        created_at: Fecha de creación del registro
        updated_at: Última fecha de modificación
    """
    
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    flavor_name: str = ""
    price: float = 0.0
    quantity: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validaciones post-construcción."""
        if not self.flavor_name or not self.flavor_name.strip():
            raise ValueError("El nombre del sabor no puede estar vacío")
        
        if self.quantity < 0:
            raise ValueError("La cantidad no puede ser negativa")
        
        if self.price < 0:
            raise ValueError("El precio no puede ser negativo")
        
        self.flavor_name = self.flavor_name.strip()
    
    def add_stock(self, amount: int) -> None:
        """Agregar stock al inventario."""
        if amount <= 0:
            raise ValueError("La cantidad a agregar debe ser mayor a 0")
        self.quantity += amount
        self.updated_at = datetime.utcnow()
    
    def remove_stock(self, amount: int) -> None:
        """Remover stock del inventario (venta)."""
        if amount <= 0:
            raise ValueError("La cantidad a remover debe ser mayor a 0")
        if amount > self.quantity:
            raise ValueError(f"No hay suficiente stock. Disponible: {self.quantity}, solicitado: {amount}")
        self.quantity -= amount
        self.updated_at = datetime.utcnow()
    
    def is_low_stock(self, threshold: int = 3) -> bool:
        """Verificar si el stock está bajo."""
        return self.quantity <= threshold
    
    def __repr__(self) -> str:
        return f"Cream(id={self.id}, flavor='{self.flavor_name}', quantity={self.quantity})"
