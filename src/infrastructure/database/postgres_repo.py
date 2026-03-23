"""
PostgreSQL Repository Implementations - Infrastructure Layer

Implementa las interfaces del dominio usando SQLAlchemy.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain import Cream, Sale, Reservation
from src.domain.repositories import CreamRepository, SaleRepository, ReservationRepository
from .base import CreamModel, SaleModel, ReservationModel


class PostgresCreamRepository(CreamRepository):
    """Implementación PostgreSQL del repositorio de cremas."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _to_entity(self, model: CreamModel) -> Cream:
        """Convertir modelo SQLAlchemy a entidad de dominio."""
        return Cream(
            id=UUID(model.id),
            flavor_name=model.flavor_name,
            price=float(model.price),
            quantity=model.quantity,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _to_model(self, entity: Cream) -> CreamModel:
        """Convertir entidad de dominio a modelo SQLAlchemy."""
        return CreamModel(
            id=str(entity.id),
            flavor_name=entity.flavor_name,
            price=float(entity.price),
            quantity=entity.quantity,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
    
    async def get_all(self) -> List[Cream]:
        result = await self.session.execute(
            select(CreamModel).order_by(CreamModel.flavor_name)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_by_id(self, cream_id: UUID) -> Optional[Cream]:
        result = await self.session.execute(
            select(CreamModel).where(CreamModel.id == str(cream_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_flavor_name(self, flavor_name: str) -> Optional[Cream]:
        result = await self.session.execute(
            select(CreamModel).where(CreamModel.flavor_name == flavor_name)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def create(self, cream: Cream) -> Cream:
        model = self._to_model(cream)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def update(self, cream: Cream) -> Cream:
        result = await self.session.execute(
            select(CreamModel).where(CreamModel.id == str(cream.id))
        )
        model = result.scalar_one_or_none()
        if model:
            model.flavor_name = cream.flavor_name
            model.price = float(cream.price)
            model.quantity = cream.quantity
            model.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(model)
            return self._to_entity(model)
        raise ValueError(f"Cream not found: {cream.id}")
    
    async def delete(self, cream_id: UUID) -> bool:
        result = await self.session.execute(
            select(CreamModel).where(CreamModel.id == str(cream_id))
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False
    
    async def get_low_stock(self, threshold: int = 3) -> List[Cream]:
        result = await self.session.execute(
            select(CreamModel)
            .where(CreamModel.quantity <= threshold)
            .order_by(CreamModel.quantity)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]


class PostgresSaleRepository(SaleRepository):
    """Implementación PostgreSQL del repositorio de ventas."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _to_entity(self, model: SaleModel) -> Sale:
        return Sale(
            id=UUID(model.id),
            cream_id=UUID(model.cream_id),
            cream_name=model.cream_name,
            quantity_sold=model.quantity_sold,
            price=model.price,
            sold_at=model.sold_at,
        )
    
    def _to_model(self, entity: Sale) -> SaleModel:
        return SaleModel(
            id=str(entity.id),
            cream_id=str(entity.cream_id),
            cream_name=entity.cream_name,
            quantity_sold=entity.quantity_sold,
            price=entity.price,
            sold_at=entity.sold_at,
        )
    
    async def get_by_cream_id(self, cream_id: UUID) -> List[Sale]:
        result = await self.session.execute(
            select(SaleModel)
            .where(SaleModel.cream_id == str(cream_id))
            .order_by(SaleModel.sold_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def create(self, sale: Sale) -> Sale:
        model = self._to_model(sale)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def get_all(self) -> List[Sale]:
        result = await self.session.execute(
            select(SaleModel).order_by(SaleModel.sold_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]


class PostgresReservationRepository(ReservationRepository):
    """Implementación PostgreSQL del repositorio de reservas."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _to_entity(self, model: ReservationModel) -> Reservation:
        return Reservation(
            id=UUID(model.id),
            cream_id=UUID(model.cream_id),
            cream_name=model.cream_name,
            quantity_reserved=model.quantity_reserved,
            reserved_for=model.reserved_for,
            customer_name=model.customer_name,
            is_active=model.is_active,
            created_at=model.created_at,
        )
    
    def _to_model(self, entity: Reservation) -> ReservationModel:
        return ReservationModel(
            id=str(entity.id),
            cream_id=str(entity.cream_id),
            cream_name=entity.cream_name,
            quantity_reserved=entity.quantity_reserved,
            reserved_for=entity.reserved_for,
            customer_name=entity.customer_name,
            is_active=entity.is_active,
            created_at=entity.created_at,
        )
    
    async def get_by_cream_id(self, cream_id: UUID) -> List[Reservation]:
        result = await self.session.execute(
            select(ReservationModel)
            .where(ReservationModel.cream_id == str(cream_id))
            .order_by(ReservationModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_active_by_cream_id(self, cream_id: UUID) -> List[Reservation]:
        result = await self.session.execute(
            select(ReservationModel)
            .where(
                and_(
                    ReservationModel.cream_id == str(cream_id),
                    ReservationModel.is_active == True
                )
            )
            .order_by(ReservationModel.reserved_for)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_active(self) -> List[Reservation]:
        result = await self.session.execute(
            select(ReservationModel)
            .where(ReservationModel.is_active == True)
            .order_by(ReservationModel.reserved_for)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def create(self, reservation: Reservation) -> Reservation:
        model = self._to_model(reservation)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def update(self, reservation: Reservation) -> Reservation:
        result = await self.session.execute(
            select(ReservationModel).where(ReservationModel.id == str(reservation.id))
        )
        model = result.scalar_one_or_none()
        if model:
            model.quantity_reserved = reservation.quantity_reserved
            model.reserved_for = reservation.reserved_for
            model.customer_name = reservation.customer_name
            model.is_active = reservation.is_active
            await self.session.commit()
            await self.session.refresh(model)
            return self._to_entity(model)
        raise ValueError(f"Reservation not found: {reservation.id}")
    
    async def delete(self, reservation_id: UUID) -> bool:
        result = await self.session.execute(
            select(ReservationModel).where(ReservationModel.id == str(reservation_id))
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False
