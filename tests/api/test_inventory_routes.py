"""
Tests for Inventory API Routes

Covers all /creams endpoints using FastAPI TestClient with dependency overrides.
"""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.domain.entities.cream import Cream
from src.domain.entities.sale import Sale
from src.domain.entities.reservation import Reservation
from src.application.services.inventory_service import InventoryService
from src.application.services.reservation_service import ReservationService
from src.infrastructure.auth import AuthUser
from tests.conftest import (
    MockCreamRepository,
    MockSaleRepository,
    MockReservationRepository,
)


# ============================================
# Mock Auth User for Tests
# ============================================

def get_mock_auth_user() -> AuthUser:
    """Returns a mock authenticated user for tests."""
    return AuthUser(
        id="test-user-123",
        email="test@example.com",
        role="authenticated",
    )


# ============================================
# Test Fixtures
# ============================================

@pytest.fixture
def mock_cream_repo() -> MockCreamRepository:
    return MockCreamRepository()


@pytest.fixture
def mock_sale_repo() -> MockSaleRepository:
    return MockSaleRepository()


@pytest.fixture
def mock_reservation_repo() -> MockReservationRepository:
    return MockReservationRepository()


@pytest.fixture
def inventory_service(
    mock_cream_repo: MockCreamRepository,
    mock_sale_repo: MockSaleRepository,
) -> InventoryService:
    return InventoryService(mock_cream_repo, mock_sale_repo)


@pytest.fixture
def reservation_service(
    mock_reservation_repo: MockReservationRepository,
    mock_cream_repo: MockCreamRepository,
) -> ReservationService:
    return ReservationService(mock_reservation_repo, mock_cream_repo)


def override_inventory_service(
    mock_cream_repo: MockCreamRepository,
    mock_sale_repo: MockSaleRepository,
) -> InventoryService:
    """Create an InventoryService with mocked repos."""
    return InventoryService(mock_cream_repo, mock_sale_repo)


def override_reservation_service(
    mock_reservation_repo: MockReservationRepository,
    mock_cream_repo: MockCreamRepository,
) -> ReservationService:
    """Create a ReservationService with mocked repos."""
    return ReservationService(mock_reservation_repo, mock_cream_repo)


# ============================================
# Helper to create mock data
# ============================================

def create_test_cream(
    mock_cream_repo: MockCreamRepository,
    flavor_name: str = "Chocolate",
    quantity: int = 10,
) -> Cream:
    """Helper that creates and stores a test cream."""
    cream = Cream(flavor_name=flavor_name, quantity=quantity)
    mock_cream_repo.add_cream(cream)
    return cream


# ============================================
# Tests
# ============================================

class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_200(self):
        """GET /health should return 200 with healthy status."""
        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCreamsEndpoints:
    """Tests for cream CRUD endpoints."""

    def test_get_creams_returns_list(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """GET /creams should return a list of creams."""
        # Arrange
        create_test_cream(mock_cream_repo, "Chocolate", 10)
        create_test_cream(mock_cream_repo, "Vainilla", 5)

        # Override dependency
        from src.api.routes.inventory import (
            get_inventory_service,
            get_reservation_service,
        )

        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.get("/creams")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
        finally:
            app.dependency_overrides.clear()

    def test_get_creams_returns_empty_list(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """GET /creams should return empty list when no creams."""
        from src.api.routes.inventory import get_inventory_service, get_reservation_service

        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.get("/creams")

            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()

    def test_post_creams_creates_cream_success(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """POST /creams should return 201 on successful creation."""
        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/creams",
                    json={"flavor_name": "Chocolate", "quantity": 10},
                )

            assert response.status_code == 201
            data = response.json()
            assert data["flavor_name"] == "Chocolate"
        finally:
            app.dependency_overrides.clear()

    def test_post_creams_rejects_duplicate(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """POST /creams should return 400 for duplicate flavor."""
        # Pre-add a cream
        create_test_cream(mock_cream_repo, "Chocolate", 5)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/creams",
                    json={"flavor_name": "Chocolate", "quantity": 10},
                )

            assert response.status_code == 400
            assert "Ya existe" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_cream_by_id_returns_404_when_not_found(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """GET /creams/{id} should return 404 for unknown ID."""
        from src.api.routes.inventory import get_inventory_service, get_reservation_service

        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        unknown_id = uuid4()
        try:
            with TestClient(app) as client:
                response = client.get(f"/creams/{unknown_id}")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_cream_by_id_returns_cream(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """GET /creams/{id} should return the cream when found."""
        cream = create_test_cream(mock_cream_repo, "Chocolate", 10)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service

        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.get(f"/creams/{cream.id}")

            assert response.status_code == 200
            assert response.json()["flavor_name"] == "Chocolate"
        finally:
            app.dependency_overrides.clear()


class TestSaleEndpoints:
    """Tests for sale endpoints."""

    def test_post_cream_sell_succeeds(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """POST /creams/{id}/sell should return 201 on success."""
        cream = create_test_cream(mock_cream_repo, "Chocolate", 10)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/creams/{cream.id}/sell",
                    json={"cream_id": str(cream.id), "quantity_sold": 3},
                )

            assert response.status_code == 201
            data = response.json()
            assert data["quantity_sold"] == 3
        finally:
            app.dependency_overrides.clear()

    def test_post_cream_sell_fails_with_id_mismatch(self):
        """POST /creams/{id}/sell should return 400 when IDs don't match."""
        path_id = uuid4()
        body_id = uuid4()

        from src.api.routes.inventory import require_auth
        app.dependency_overrides[require_auth] = get_mock_auth_user
        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/creams/{path_id}/sell",
                    json={"cream_id": str(body_id), "quantity_sold": 3},
                )

            assert response.status_code == 400
            assert "coincidir" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_post_cream_sell_fails_with_insufficient_stock(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """POST /creams/{id}/sell should return 400 for insufficient stock."""
        cream = create_test_cream(mock_cream_repo, "Chocolate", 2)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/creams/{cream.id}/sell",
                    json={"cream_id": str(cream.id), "quantity_sold": 5},
                )

            assert response.status_code == 400
            assert "insuficiente" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestReservationEndpoints:
    """Tests for reservation endpoints."""

    def test_post_cream_reserve_creates_reservation(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_reservation_repo: MockReservationRepository,
    ):
        """POST /creams/{id}/reserve should return 201 on success."""
        cream = create_test_cream(mock_cream_repo, "Chocolate", 10)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, MockSaleRepository()
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            mock_reservation_repo, mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/creams/{cream.id}/reserve",
                    json={
                        "cream_id": str(cream.id),
                        "quantity_reserved": 3,
                        "reserved_for": str(date.today()),
                    },
                )

            assert response.status_code == 201
            data = response.json()
            assert data["quantity_reserved"] == 3
            assert data["is_active"] is True
        finally:
            app.dependency_overrides.clear()

    def test_post_reservation_deliver_succeeds(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_reservation_repo: MockReservationRepository,
    ):
        """POST /creams/reservations/{id}/deliver should return 200 on success."""
        cream = create_test_cream(mock_cream_repo, "Chocolate", 10)
        reservation = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=3,
            reserved_for=date.today(),
        )
        mock_reservation_repo.add_reservation(reservation)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, MockSaleRepository()
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            mock_reservation_repo, mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.post(f"/creams/reservations/{reservation.id}/deliver")

            assert response.status_code == 200
            assert response.json()["message"] == "Reserva entregada correctamente"
        finally:
            app.dependency_overrides.clear()

    def test_post_reservation_deliver_returns_404_when_not_found(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_reservation_repo: MockReservationRepository,
    ):
        """POST /creams/reservations/{id}/deliver should return 404 if not found."""
        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, MockSaleRepository()
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            mock_reservation_repo, mock_cream_repo
        )

        reservation_id = uuid4()
        try:
            with TestClient(app) as client:
                response = client.post(f"/creams/reservations/{reservation_id}/deliver")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_post_reservation_cancel_succeeds(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_reservation_repo: MockReservationRepository,
    ):
        """POST /creams/reservations/{id}/cancel should return 200 on success."""
        cream = create_test_cream(mock_cream_repo, "Chocolate", 10)
        reservation = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=3,
            reserved_for=date.today(),
        )
        mock_reservation_repo.add_reservation(reservation)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service, require_auth

        app.dependency_overrides[require_auth] = get_mock_auth_user
        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, MockSaleRepository()
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            mock_reservation_repo, mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.post(f"/creams/reservations/{reservation.id}/cancel")

            assert response.status_code == 200
            assert response.json()["message"] == "Reserva cancelada correctamente"
        finally:
            app.dependency_overrides.clear()


class TestLowStockEndpoint:
    """Tests for /creams/low-stock endpoint."""

    def test_get_low_stock_returns_alerts(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """GET /creams/low-stock should return alerts with count."""
        # Add a low-stock cream
        create_test_cream(mock_cream_repo, "Chocolate", 1)
        # Add a normal cream
        create_test_cream(mock_cream_repo, "Vainilla", 10)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service

        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.get("/creams/low-stock")

            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert "total" in data
            # Only the low-stock cream should be in alerts
            assert data["total"] == 1
            assert data["alerts"][0]["flavor_name"] == "Chocolate"
        finally:
            app.dependency_overrides.clear()

    def test_get_low_stock_empty_when_no_low_stock(
        self,
        mock_cream_repo: MockCreamRepository,
        mock_sale_repo: MockSaleRepository,
    ):
        """GET /creams/low-stock should return empty alerts when none low."""
        # Add only normal-stock creams
        create_test_cream(mock_cream_repo, "Chocolate", 10)
        create_test_cream(mock_cream_repo, "Vainilla", 5)

        from src.api.routes.inventory import get_inventory_service, get_reservation_service

        app.dependency_overrides[get_inventory_service] = lambda: override_inventory_service(
            mock_cream_repo, mock_sale_repo
        )
        app.dependency_overrides[get_reservation_service] = lambda: override_reservation_service(
            MockReservationRepository(), mock_cream_repo
        )

        try:
            with TestClient(app) as client:
                response = client.get("/creams/low-stock")

            assert response.status_code == 200
            data = response.json()
            assert data["alerts"] == []
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()
