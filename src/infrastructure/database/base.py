"""
Database Base - Infrastructure Layer

Define los modelos SQLAlchemy y la configuración de la base de datos.
"""
from datetime import datetime, date
from typing import AsyncGenerator

from sqlalchemy import (
    create_engine,
    DateTime,
    Date,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Index,
    Numeric,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from ..config.settings import settings


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy."""
    pass


# ============================================
# Modelos SQLAlchemy (Tablas de la DB)
# ============================================


class CreamModel(Base):
    """Modelo SQLAlchemy para la tabla de cremas."""
    
    __tablename__ = "creams"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    flavor_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        Index("ix_creams_quantity", "quantity"),
        Index("ix_creams_updated_at", "updated_at"),
    )
    
    # Relaciones
    sales: Mapped[list["SaleModel"]] = relationship(
        "SaleModel", 
        back_populates="cream",
        cascade="all, delete-orphan"
    )
    reservations: Mapped[list["ReservationModel"]] = relationship(
        "ReservationModel",
        back_populates="cream",
        cascade="all, delete-orphan"
    )


class SaleModel(Base):
    """Modelo SQLAlchemy para la tabla de ventas."""
    
    __tablename__ = "sales"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cream_id: Mapped[str] = mapped_column(String(36), ForeignKey("creams.id"), nullable=False)
    cream_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_sales_cream_id", "cream_id"),
        Index("ix_sales_sold_at", "sold_at"),
    )
    
    # Relaciones
    cream: Mapped["CreamModel"] = relationship("CreamModel", back_populates="sales")


class ReservationModel(Base):
    """Modelo SQLAlchemy para la tabla de reservas/apartados."""
    
    __tablename__ = "reservations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cream_id: Mapped[str] = mapped_column(String(36), ForeignKey("creams.id"), nullable=False)
    cream_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_for: Mapped[date] = mapped_column(Date, nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_reservations_cream_id", "cream_id"),
        Index("ix_reservations_is_active", "is_active"),
        Index("ix_reservations_reserved_for", "reserved_for"),
        Index("ix_reservations_active_date", "is_active", "reserved_for"),
    )
    
    # Relaciones
    cream: Mapped["CreamModel"] = relationship("CreamModel", back_populates="reservations")


# ============================================
# Configuración del Async Engine
# ============================================

# Crear engine async
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
)

# Crear session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión de base de datos.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Inicializar la base de datos (crear tablas)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Eliminar todas las tablas (para desarrollo)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
