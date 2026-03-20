"""
Pytest Configuration and Fixtures

Provides mock repositories, service fixtures, and Phase 5 test fixtures
for infrastructure (auth, cache) and services (inventory, notification).
"""
from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch

import pytest
from cachetools import TTLCache

from src.domain.entities.cream import Cream
from src.domain.entities.sale import Sale
from src.domain.entities.reservation import Reservation
from src.domain.repositories import CreamRepository, SaleRepository, ReservationRepository
from src.application.services.inventory_service import InventoryService
from src.application.services.reservation_service import ReservationService
from src.infrastructure.auth import AuthUser
from src.infrastructure.cache import MemoryCache


# ============================================
# Mock Cream Repository
# ============================================

class MockCreamRepository(CreamRepository):
    """Concrete mock implementing CreamRepository ABC."""

    def __init__(self):
        self._creams: Dict[UUID, Cream] = {}

    async def get_all(self) -> List[Cream]:
        return list(self._creams.values())

    async def get_by_id(self, cream_id: UUID) -> Optional[Cream]:
        return self._creams.get(cream_id)

    async def get_by_flavor_name(self, flavor_name: str) -> Optional[Cream]:
        for cream in self._creams.values():
            if cream.flavor_name.lower() == flavor_name.lower():
                return cream
        return None

    async def create(self, cream: Cream) -> Cream:
        self._creams[cream.id] = cream
        return cream

    async def update(self, cream: Cream) -> Cream:
        self._creams[cream.id] = cream
        return cream

    async def delete(self, cream_id: UUID) -> bool:
        if cream_id in self._creams:
            del self._creams[cream_id]
            return True
        return False

    async def get_low_stock(self, threshold: int = 3) -> List[Cream]:
        return [c for c in self._creams.values() if c.is_low_stock(threshold)]

    # Helper to populate with a cream
    def add_cream(self, cream: Cream) -> None:
        self._creams[cream.id] = cream


# ============================================
# Mock Sale Repository
# ============================================

class MockSaleRepository(SaleRepository):
    """Concrete mock implementing SaleRepository ABC."""

    def __init__(self):
        self._sales: Dict[UUID, Sale] = {}

    async def get_by_cream_id(self, cream_id: UUID) -> List[Sale]:
        return [s for s in self._sales.values() if s.cream_id == cream_id]

    async def create(self, sale: Sale) -> Sale:
        self._sales[sale.id] = sale
        return sale

    async def get_all(self) -> List[Sale]:
        return list(self._sales.values())


# ============================================
# Mock Reservation Repository
# ============================================

class MockReservationRepository(ReservationRepository):
    """Concrete mock implementing ReservationRepository ABC."""

    def __init__(self):
        self._reservations: Dict[UUID, Reservation] = {}

    async def get_by_cream_id(self, cream_id: UUID) -> List[Reservation]:
        return [r for r in self._reservations.values() if r.cream_id == cream_id]

    async def get_active_by_cream_id(self, cream_id: UUID) -> List[Reservation]:
        return [
            r for r in self._reservations.values()
            if r.cream_id == cream_id and r.is_active
        ]

    async def get_active(self) -> List[Reservation]:
        return [r for r in self._reservations.values() if r.is_active]

    async def create(self, reservation: Reservation) -> Reservation:
        self._reservations[reservation.id] = reservation
        return reservation

    async def update(self, reservation: Reservation) -> Reservation:
        self._reservations[reservation.id] = reservation
        return reservation

    async def delete(self, reservation_id: UUID) -> bool:
        if reservation_id in self._reservations:
            del self._reservations[reservation_id]
            return True
        return False

    # Helper to populate with a reservation
    def add_reservation(self, reservation: Reservation) -> None:
        self._reservations[reservation.id] = reservation


# ============================================
# Pytest Fixtures
# ============================================

@pytest.fixture
def mock_cream_repo() -> MockCreamRepository:
    """Provides a fresh MockCreamRepository for each test."""
    return MockCreamRepository()


@pytest.fixture
def mock_sale_repo() -> MockSaleRepository:
    """Provides a fresh MockSaleRepository for each test."""
    return MockSaleRepository()


@pytest.fixture
def mock_reservation_repo() -> MockReservationRepository:
    """Provides a fresh MockReservationRepository for each test."""
    return MockReservationRepository()


@pytest.fixture
def inventory_service(
    mock_cream_repo: MockCreamRepository,
    mock_sale_repo: MockSaleRepository,
) -> InventoryService:
    """Provides an InventoryService with mocked repositories."""
    return InventoryService(mock_cream_repo, mock_sale_repo)


@pytest.fixture
def reservation_service(
    mock_reservation_repo: MockReservationRepository,
    mock_cream_repo: MockCreamRepository,
) -> ReservationService:
    """Provides a ReservationService with mocked repositories."""
    return ReservationService(mock_reservation_repo, mock_cream_repo)


@pytest.fixture
def sample_cream(mock_cream_repo: MockCreamRepository) -> Cream:
    """Provides a pre-created sample cream."""
    cream = Cream(flavor_name="Chocolate", quantity=10)
    mock_cream_repo.add_cream(cream)
    return cream


@pytest.fixture
def sample_sale(mock_sale_repo: MockSaleRepository, sample_cream: Cream) -> Sale:
    """Provides a pre-created sample sale."""
    sale = Sale(
        cream_id=sample_cream.id,
        cream_name=sample_cream.flavor_name,
        quantity_sold=2,
    )
    mock_sale_repo._sales[sale.id] = sale
    return sale


@pytest.fixture
def sample_reservation(
    mock_reservation_repo: MockReservationRepository,
    sample_cream: Cream,
) -> Reservation:
    """Provides a pre-created sample reservation."""
    reservation = Reservation(
        cream_id=sample_cream.id,
        cream_name=sample_cream.flavor_name,
        quantity_reserved=3,
        reserved_for=date.today(),
    )
    mock_reservation_repo.add_reservation(reservation)
    return reservation


# ============================================
# Phase 5: Testing Fixtures
# ============================================

@pytest.fixture
def test_settings():
    """
    Provides a settings dict with debug=True and cache_enabled=True
    for testing without relying on config.yaml or .env.
    """
    return {
        "debug": True,
        "cache_enabled": True,
        "low_stock_threshold": 3,
        "supabase_url": "https://test-project.supabase.co",
        "jwks_cache_ttl": 60,
        "jwks_fetch_timeout": 5,
    }


@pytest.fixture
def cache_client() -> MemoryCache:
    """
    Provides a fresh in-memory TTLCache instance for testing.
    
    Uses a short TTL (2s) to make expiry tests fast.
    """
    return MemoryCache(maxsize=128, ttl=2)


@pytest.fixture
def auth_mock():
    """
    Provides an async mock for verify_supabase_token that returns a valid AuthUser.
    
    The mock is an async function (coroutine) that returns an AuthUser with
    known test values when awaited. Replace with a different return value or
    side_effect to simulate different outcomes:
    - Valid token: returns AuthUser(...)
    - Invalid/expired: returns None
    - Exception: use side_effect = SomeException()
    """
    async def mock_verify(token: str) -> AuthUser:
        return AuthUser(
            id="test-user-id",
            email="test@gentleman.com",
            role="authenticated",
            raw_token=token,
        )

    return mock_verify


# ============================================
# Fake AuthUser for direct injection in tests
# ============================================

@pytest.fixture
def fake_auth_user() -> AuthUser:
    """Provides a fake AuthUser for direct use in tests."""
    return AuthUser(
        id="fake-user-uuid",
        email="fake@test.com",
        role="authenticated",
        raw_token="fake-jwt-token",
    )
