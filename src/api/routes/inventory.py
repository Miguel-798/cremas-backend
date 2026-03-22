"""
Inventory Routes - API Layer

Endpoints para gestionar el inventario de cremas.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.infrastructure.database import get_db
from src.infrastructure.database.postgres_repo import (
    PostgresCreamRepository,
    PostgresSaleRepository,
    PostgresReservationRepository,
)
from src.infrastructure.auth import AuthUser, verify_supabase_token
from src.application.services import (
    InventoryService,
    ReservationService,
    NotificationService,
)
from src.application.dtos import (
    CreamCreate,
    CreamUpdate,
    CreamAddStock,
    CreamResponse,
    CreamWithStatus,
    SaleCreate,
    SaleResponse,
    ReservationCreate,
    ReservationActivate,
    ReservationResponse,
    LowStockAlert,
    LowStockResponse,
    CreamHistoryResponse,
)
from src.infrastructure.config import settings
from src.infrastructure.logging import get_logger

log = get_logger(__name__)


# ============================================
# Rate Limiter
# ============================================

def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on user or IP."""
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.id}"
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key)


# ============================================
# Router and Dependencies
# ============================================

# Router with /creams prefix
router = APIRouter(prefix="/creams", tags=["inventory"])

# Router without prefix for special endpoints
sales_router = APIRouter(tags=["sales"])

# HTTPBearer scheme for optional auth (no auto-error)
optional_bearer = HTTPBearer(auto_error=False)


def get_inventory_service(db: AsyncSession = Depends(get_db)) -> InventoryService:
    """Dependency para obtener el servicio de inventario."""
    cream_repo = PostgresCreamRepository(db)
    sale_repo = PostgresSaleRepository(db)
    return InventoryService(cream_repo, sale_repo)


def get_reservation_service(db: AsyncSession = Depends(get_db)) -> ReservationService:
    """Dependency para obtener el servicio de reservas."""
    reservation_repo = PostgresReservationRepository(db)
    cream_repo = PostgresCreamRepository(db)
    return ReservationService(reservation_repo, cream_repo)


def get_notification_service() -> NotificationService:
    """Dependency para obtener el servicio de notificaciones."""
    return NotificationService()


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
) -> AuthUser:
    """
    Dependency que requiere autenticación.
    
    Returns the AuthUser or raises 401.
    """
    log.debug("auth.credentials_received", has_credentials=credentials is not None)
    
    if credentials is None:
        log.warning("auth.missing_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    log.debug("auth.token_received", token_prefix=credentials.credentials[:20])
    
    user = await verify_supabase_token(credentials.credentials)
    if user is None:
        log.warning("auth.token_verification_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    log.debug("auth.user_authenticated", user_id=user.id, email=user.email)
    return user


async def get_optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
) -> Optional[AuthUser]:
    """
    Dependency para autenticación opcional.
    
    Returns AuthUser if valid token, None otherwise.
    """
    if credentials is None:
        return None
    
    return await verify_supabase_token(credentials.credentials)


# ============================================
# Cream Endpoints - ORDEN IMPORTANTE
# Las rutas más específicas van primero
# Rate Limits:
#   - READ operations: 60/min
#   - WRITE operations: 20/min
#   - Authenticated users get separate limits
# ============================================


# 1. GET /creams - Obtener todas las cremas (requiere auth)
@router.get("", response_model=List[CreamWithStatus])
@limiter.limit("60/minute")
async def get_all_creams(
    request: Request,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Obtener todas las cremas del inventario."""
    request.state.user = user
    
    creams = await service.get_all_creams()
    threshold = settings.low_stock_threshold
    return [
        CreamWithStatus(
            id=c.id,
            flavor_name=c.flavor_name,
            price=c.price,
            quantity=c.quantity,
            is_low_stock=c.is_low_stock(threshold),
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in creams
    ]


# 2. GET /creams/low-stock - Alertas de stock (antes de /{cream_id})
@router.get("/low-stock", response_model=LowStockResponse)
@limiter.limit("60/minute")
async def get_low_stock(
    request: Request,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Obtener lista de cremas con stock bajo (≤3)."""
    request.state.user = user
    
    low_stock_creams = await service.get_low_stock_creams()
    
    alerts = [
        LowStockAlert(
            cream_id=c.id,
            flavor_name=c.flavor_name,
            current_quantity=c.quantity,
            threshold=settings.low_stock_threshold,
        )
        for c in low_stock_creams
    ]
    
    return LowStockResponse(alerts=alerts, total=len(alerts))


# 3. POST /creams - Crear nueva crema (requiere auth)
@router.post("", response_model=CreamResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_cream(
    request: Request,
    data: CreamCreate,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Crear una nueva crema/sabor."""
    try:
        cream = await service.create_cream(
            flavor_name=data.flavor_name,
            price=data.price,
            quantity=data.quantity,
        )
        return CreamResponse.model_validate(cream)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 4. GET /creams/{cream_id} - Obtener una crema por ID (público)
@router.get("/{cream_id}", response_model=CreamResponse)
async def get_cream(
    cream_id: UUID,
    request: Request,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Obtener una crema por su ID."""
    request.state.user = user
    
    cream = await service.get_cream_by_id(cream_id)
    if not cream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crema no encontrada: {cream_id}"
        )
    return CreamResponse.model_validate(cream)


# 5. PUT /creams/{cream_id} - Actualizar cantidad (requiere auth)
@router.put("/{cream_id}", response_model=CreamResponse)
@limiter.limit("20/minute")
async def update_cream(
    request: Request,
    cream_id: UUID,
    data: CreamUpdate,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Actualizar la cantidad de una crema."""
    try:
        cream = await service.update_cream_quantity(cream_id, data.quantity)
        return CreamResponse.model_validate(cream)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# 6. POST /creams/{cream_id}/add-stock - Agregar stock (requiere auth)
@router.post("/{cream_id}/add-stock", response_model=CreamResponse)
@limiter.limit("20/minute")
async def add_stock(
    request: Request,
    cream_id: UUID,
    data: CreamAddStock,
    service: InventoryService = Depends(get_inventory_service),
    notif_service: NotificationService = Depends(get_notification_service),
    user: AuthUser = Depends(require_auth),
):
    """Agregar stock a una crema."""
    try:
        cream = await service.add_stock(cream_id, data.amount)
        
        # Check for low stock after adding
        low_stock = await service.get_low_stock_creams()
        if low_stock and service.check_low_stock(cream):
            await notif_service.send_low_stock_alert(low_stock)
        
        return CreamResponse.model_validate(cream)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# 7. DELETE /creams/{cream_id} - Eliminar crema (requiere auth)
@router.delete("/{cream_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_cream(
    request: Request,
    cream_id: UUID,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Eliminar una crema del inventario."""
    deleted = await service.delete_cream(cream_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crema no encontrada: {cream_id}"
        )


# ============================================
# Sale Endpoints
# ============================================

# GET /creamssales - Obtener todas las ventas (fuera del prefijo /creams)
@sales_router.get("/creamssales", response_model=List[SaleResponse])
@limiter.limit("60/minute")
async def get_all_sales(
    request: Request,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Obtener todas las ventas."""
    request.state.user = user
    
    sales = await service.get_all_sales()
    return [SaleResponse.model_validate(s) for s in sales]


# 9. POST /creams/{cream_id}/sell - Registrar venta (requiere auth)
@router.post("/{cream_id}/sell", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def register_sale(
    request: Request,
    cream_id: UUID,
    data: SaleCreate,
    service: InventoryService = Depends(get_inventory_service),
    notif_service: NotificationService = Depends(get_notification_service),
    user: AuthUser = Depends(require_auth),
):
    """Registrar una venta."""
    if cream_id != data.cream_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID de la crema en el path debe coincidir con el del body"
        )
    
    try:
        sale = await service.register_sale(cream_id, data.quantity_sold)
        
        # Check for low stock after sale
        low_stock = await service.get_low_stock_creams()
        if low_stock:
            await notif_service.send_low_stock_alert(low_stock)
        
        return SaleResponse.model_validate(sale)
    except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


# 10. GET /creams/{cream_id}/sales - Historial de ventas (público)
@router.get("/{cream_id}/sales", response_model=List[SaleResponse])
async def get_cream_sales(
    cream_id: UUID,
    request: Request,
    service: InventoryService = Depends(get_inventory_service),
    user: AuthUser = Depends(require_auth),
):
    """Obtener historial de ventas de una crema."""
    request.state.user = user
    
    cream = await service.get_cream_by_id(cream_id)
    if not cream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crema no encontrada: {cream_id}"
        )
    
    sales = await service.get_sales_by_cream(cream_id)
    return [SaleResponse.model_validate(s) for s in sales]


# ============================================
# Reservation Endpoints
# ============================================


# 11. POST /creams/{cream_id}/reserve - Crear reserva (requiere auth)
@router.post("/{cream_id}/reserve", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_reservation(
    request: Request,
    cream_id: UUID,
    data: ReservationCreate,
    reservation_service: ReservationService = Depends(get_reservation_service),
    user: AuthUser = Depends(require_auth),
):
    """Crear una nueva reserva/apartado."""
    if cream_id != data.cream_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID de la crema en el path debe coincidir con el del body"
        )
    
    try:
        reservation = await reservation_service.create_reservation(
            cream_id=data.cream_id,
            quantity_reserved=data.quantity_reserved,
            reserved_for=data.reserved_for,
            customer_name=data.customer_name,
        )
        return ReservationResponse.model_validate(reservation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 12. POST /creams/{cream_id}/reserve/activate - Reactivar reserva (requiere auth)
@router.post("/{cream_id}/reserve/activate", response_model=ReservationResponse)
@limiter.limit("20/minute")
async def activate_reservation(
    request: Request,
    cream_id: UUID,
    data: ReservationActivate,
    reservation_service: ReservationService = Depends(get_reservation_service),
    user: AuthUser = Depends(require_auth),
):
    """Reactivar una reserva existente o crear una nueva."""
    try:
        reservation = await reservation_service.activate_reservation(
            cream_id=cream_id,
            quantity_reserved=data.quantity_reserved,
            reserved_for=data.reserved_for,
            customer_name=data.customer_name,
        )
        return ReservationResponse.model_validate(reservation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 13. GET /creams/reservations/active - Reservas activas (antes de /{reservation_id})
@router.get("/reservations/active", response_model=List[ReservationResponse])
@limiter.limit("60/minute")
async def get_active_reservations(
    request: Request,
    reservation_service: ReservationService = Depends(get_reservation_service),
    user: AuthUser = Depends(require_auth),
):
    """Obtener todas las reservas activas."""
    request.state.user = user
    
    reservations = await reservation_service.get_active_reservations()
    return [ReservationResponse.model_validate(r) for r in reservations]


# 14. POST /creams/reservations/{reservation_id}/deliver - Entregar reserva (requiere auth)
@router.post("/reservations/{reservation_id}/deliver")
@limiter.limit("20/minute")
async def deliver_reservation(
    request: Request,
    reservation_id: UUID,
    reservation_service: ReservationService = Depends(get_reservation_service),
    user: AuthUser = Depends(require_auth),
):
    """Entregar una reserva (marca como entregada y descuenta stock)."""
    try:
        await reservation_service.deliver_reservation(reservation_id)
        return {"message": "Reserva entregada correctamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# 15. POST /creams/reservations/{reservation_id}/cancel - Cancelar reserva (requiere auth)
@router.post("/reservations/{reservation_id}/cancel")
@limiter.limit("20/minute")
async def cancel_reservation(
    request: Request,
    reservation_id: UUID,
    reservation_service: ReservationService = Depends(get_reservation_service),
    user: AuthUser = Depends(require_auth),
):
    """Cancelar una reserva."""
    cancelled = await reservation_service.cancel_reservation(reservation_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva no encontrada: {reservation_id}"
        )
    return {"message": "Reserva cancelada correctamente"}


# ============================================
# History Endpoints
# ============================================


# 16. GET /creams/{cream_id}/history - Historial completo (público)
@router.get("/{cream_id}/history", response_model=CreamHistoryResponse)
async def get_cream_history(
    cream_id: UUID,
    request: Request,
    service: InventoryService = Depends(get_inventory_service),
    reservation_service: ReservationService = Depends(get_reservation_service),
    user: AuthUser = Depends(require_auth),
):
    """Obtener historial completo de una crema (ventas y reservas)."""
    request.state.user = user
    
    cream = await service.get_cream_by_id(cream_id)
    if not cream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crema no encontrada: {cream_id}"
        )
    
    sales = await service.get_sales_by_cream(cream_id)
    reservations = await reservation_service.get_reservations_by_cream(cream_id)
    
    return CreamHistoryResponse(
        cream=CreamResponse.model_validate(cream),
        sales=[SaleResponse.model_validate(s) for s in sales],
        reservations=[ReservationResponse.model_validate(r) for r in reservations],
    )
