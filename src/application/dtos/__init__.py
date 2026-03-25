"""
DTOs - Application Layer

Data Transfer Objects para la API.
"""
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, field_serializer


# Pydantic config for timezone-aware datetime handling
DTOS_CONFIG = ConfigDict(
    from_attributes=True,
)


# Field serializer for datetime fields - ensures ISO 8601 format with timezone
def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO 8601 string."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.isoformat()
    return dt.isoformat()


# ============================================
# Cream DTOs
# ============================================


class CreamCreate(BaseModel):
    """DTO para crear una nueva crema."""
    flavor_name: str = Field(..., min_length=1, max_length=255, description="Nombre del sabor")
    price: float = Field(default=0.0, ge=0, description="Precio de la crema")
    quantity: int = Field(default=0, ge=0, description="Cantidad inicial")


class CreamUpdate(BaseModel):
    """DTO para actualizar cantidad de crema."""
    quantity: int = Field(..., ge=0, description="Nueva cantidad")


class CreamAddStock(BaseModel):
    """DTO para agregar stock."""
    amount: int = Field(..., gt=0, description="Cantidad a agregar")


class CreamResponse(BaseModel):
    """DTO para responder con datos de crema."""
    id: UUID
    flavor_name: str
    price: float
    quantity: int
    created_at: datetime
    updated_at: datetime
    
    model_config = DTOS_CONFIG
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO 8601 string."""
        if dt is None:
            return None
        return dt.isoformat()


class CreamWithStatus(BaseModel):
    """DTO para crema con estado de alerta."""
    id: UUID
    flavor_name: str
    price: float
    quantity: int
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = DTOS_CONFIG
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO 8601 string."""
        if dt is None:
            return None
        return dt.isoformat()


# ============================================
# Sale DTOs
# ============================================


class SaleCreate(BaseModel):
    """DTO para registrar una venta."""
    cream_id: UUID = Field(..., description="ID de la crema")
    quantity_sold: int = Field(..., gt=0, description="Cantidad vendida")
    price: Optional[float] = Field(None, description="Precio manual (opcional)")


class SaleResponse(BaseModel):
    """DTO para responder con datos de venta."""
    id: UUID
    cream_id: UUID
    cream_name: str
    quantity_sold: int
    price: float = 0.0
    total: float = 0.0
    sold_at: datetime
    
    model_config = DTOS_CONFIG
    
    @field_serializer('sold_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO 8601 string."""
        if dt is None:
            return None
        return dt.isoformat()
    
    @model_validator(mode='after')
    def compute_total(self):
        """Compute total automatically from price × quantity if not provided."""
        if self.total == 0 and self.price > 0:
            self.total = self.price * self.quantity_sold
        return self


# ============================================
# Reservation DTOs
# ============================================


class ReservationCreate(BaseModel):
    """DTO para crear una reserva."""
    cream_id: UUID = Field(..., description="ID de la crema")
    quantity_reserved: int = Field(..., gt=0, description="Cantidad a apartar")
    reserved_for: date = Field(..., description="Fecha para la que se apartan")
    customer_name: Optional[str] = Field(None, max_length=255, description="Nombre del cliente")


class ReservationUpdate(BaseModel):
    """DTO para actualizar una reserva."""
    quantity_reserved: Optional[int] = Field(None, gt=0, description="Nueva cantidad")
    reserved_for: Optional[date] = Field(None, description="Nueva fecha")
    customer_name: Optional[str] = Field(None, max_length=255, description="Nuevo nombre")


class ReservationResponse(BaseModel):
    """DTO para responder con datos de reserva."""
    id: UUID
    cream_id: UUID
    cream_name: str
    quantity_reserved: int
    reserved_for: date
    customer_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    model_config = DTOS_CONFIG
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO 8601 string."""
        if dt is None:
            return None
        return dt.isoformat()


class ReservationActivate(BaseModel):
    """DTO para activar/reactivar una reserva."""
    quantity_reserved: int = Field(..., gt=0, description="Cantidad a reservar")
    reserved_for: date = Field(..., description="Fecha para la que se apartan")
    customer_name: Optional[str] = Field(None, max_length=255, description="Nombre del cliente")


# ============================================
# Alert DTOs
# ============================================


class LowStockAlert(BaseModel):
    """DTO para alerta de stock bajo."""
    cream_id: UUID
    flavor_name: str
    current_quantity: int
    threshold: int
    
    model_config = ConfigDict(from_attributes=True)


class LowStockResponse(BaseModel):
    """DTO para respuesta de alertas."""
    alerts: list[LowStockAlert]
    total: int


# ============================================
# History DTOs
# ============================================


class CreamHistoryResponse(BaseModel):
    """DTO para historial de una crema."""
    cream: CreamResponse
    sales: list[SaleResponse]
    reservations: list[ReservationResponse]
