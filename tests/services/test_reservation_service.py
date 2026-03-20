"""
Tests for ReservationService

Covers reservation creation, delivery, cancellation, and expiry.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from src.domain.entities.cream import Cream
from src.domain.entities.reservation import Reservation
from src.application.services.reservation_service import ReservationService
from tests.conftest import MockCreamRepository, MockReservationRepository


class TestReservationServiceCreate:
    """Tests for ReservationService.create_reservation."""

    @pytest.mark.asyncio
    async def test_create_reservation_fails_when_cream_not_found(
        self,
        reservation_service: ReservationService,
    ):
        """create_reservation should raise ValueError when cream doesn't exist."""
        with pytest.raises(ValueError, match="no encontrada"):
            await reservation_service.create_reservation(
                cream_id=uuid4(),
                quantity_reserved=3,
                reserved_for=date.today(),
            )

    @pytest.mark.asyncio
    async def test_create_reservation_fails_with_past_date(
        self,
        reservation_service: ReservationService,
        mock_cream_repo: MockCreamRepository,
    ):
        """create_reservation should raise ValueError for past dates."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=10)
        mock_cream_repo.add_cream(cream)
        past_date = date.today() - timedelta(days=1)

        # Act & Assert
        with pytest.raises(ValueError, match="anterior a hoy"):
            await reservation_service.create_reservation(
                cream_id=cream.id,
                quantity_reserved=3,
                reserved_for=past_date,
            )

    @pytest.mark.asyncio
    async def test_create_reservation_fails_with_insufficient_stock(
        self,
        reservation_service: ReservationService,
        mock_cream_repo: MockCreamRepository,
    ):
        """create_reservation should raise ValueError when stock is insufficient."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=2)
        mock_cream_repo.add_cream(cream)

        # Act & Assert
        with pytest.raises(ValueError, match="insuficiente"):
            await reservation_service.create_reservation(
                cream_id=cream.id,
                quantity_reserved=5,
                reserved_for=date.today(),
            )

    @pytest.mark.asyncio
    async def test_create_reservation_succeeds(
        self,
        reservation_service: ReservationService,
        mock_cream_repo: MockCreamRepository,
        mock_reservation_repo: MockReservationRepository,
    ):
        """create_reservation should succeed and create reservation in repo."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=10)
        mock_cream_repo.add_cream(cream)

        # Act
        reservation = await reservation_service.create_reservation(
            cream_id=cream.id,
            quantity_reserved=3,
            reserved_for=date.today(),
            customer_name="Juan",
        )

        # Assert
        assert reservation.cream_id == cream.id
        assert reservation.cream_name == "Chocolate"
        assert reservation.quantity_reserved == 3
        assert reservation.is_active is True
        assert reservation.customer_name == "Juan"

        # Verify it was stored in repo
        saved = await mock_reservation_repo.get_by_cream_id(cream.id)
        assert len(saved) == 1
        assert saved[0].id == reservation.id

    @pytest.mark.asyncio
    async def test_create_reservation_with_future_date_succeeds(
        self,
        reservation_service: ReservationService,
        mock_cream_repo: MockCreamRepository,
    ):
        """create_reservation should accept future reserved_for dates."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=10)
        mock_cream_repo.add_cream(cream)
        future_date = date.today() + timedelta(days=5)

        # Act
        reservation = await reservation_service.create_reservation(
            cream_id=cream.id,
            quantity_reserved=3,
            reserved_for=future_date,
        )

        # Assert
        assert reservation.reserved_for == future_date


class TestReservationServiceDeliver:
    """Tests for ReservationService.deliver_reservation."""

    @pytest.mark.asyncio
    async def test_deliver_reservation_decrements_stock_and_deactivates(
        self,
        reservation_service: ReservationService,
        mock_reservation_repo: MockReservationRepository,
        mock_cream_repo: MockCreamRepository,
    ):
        """deliver_reservation should decrement stock and mark as inactive."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=10)
        mock_cream_repo.add_cream(cream)

        reservation = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=3,
            reserved_for=date.today(),
        )
        mock_reservation_repo.add_reservation(reservation)

        # Act
        result = await reservation_service.deliver_reservation(reservation.id)

        # Assert
        assert result is True

        # Stock should be decremented
        updated_cream = await mock_cream_repo.get_by_id(cream.id)
        assert updated_cream.quantity == 7

        # Reservation should be deactivated
        updated_res = await mock_reservation_repo.get_by_cream_id(cream.id)
        assert len(updated_res) == 1
        assert updated_res[0].is_active is False

    @pytest.mark.asyncio
    async def test_deliver_reservation_fails_for_nonexistent(
        self,
        reservation_service: ReservationService,
    ):
        """deliver_reservation should raise ValueError for unknown reservation."""
        with pytest.raises(ValueError, match="no encontrada"):
            await reservation_service.deliver_reservation(uuid4())


class TestReservationServiceCancel:
    """Tests for ReservationService.cancel_reservation."""

    @pytest.mark.asyncio
    async def test_cancel_reservation_marks_inactive(
        self,
        reservation_service: ReservationService,
        mock_reservation_repo: MockReservationRepository,
        sample_reservation: Reservation,
    ):
        """cancel_reservation should mark the reservation as inactive."""
        # Act
        result = await reservation_service.cancel_reservation(sample_reservation.id)

        # Assert
        assert result is True

        # Reservation should be inactive
        updated = await mock_reservation_repo.get_by_cream_id(sample_reservation.cream_id)
        assert len(updated) == 1
        assert updated[0].is_active is False

    @pytest.mark.asyncio
    async def test_cancel_reservation_returns_false_when_not_found(
        self,
        reservation_service: ReservationService,
    ):
        """cancel_reservation should return False when reservation not found."""
        result = await reservation_service.cancel_reservation(uuid4())
        assert result is False


class TestReservationServiceExpired:
    """Tests for ReservationService.get_expired_reservations and expire_reservations."""

    @pytest.mark.asyncio
    async def test_get_expired_reservations_filters_correctly(
        self,
        reservation_service: ReservationService,
        mock_reservation_repo: MockReservationRepository,
        mock_cream_repo: MockCreamRepository,
    ):
        """get_expired_reservations should only return expired reservations."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=10)
        mock_cream_repo.add_cream(cream)

        # Active but not expired
        active = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=2,
            reserved_for=date.today(),
        )

        # Expired (reserved 10 days ago, expiry is 2 days)
        expired = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=2,
            reserved_for=date.today() - timedelta(days=10),
        )

        mock_reservation_repo.add_reservation(active)
        mock_reservation_repo.add_reservation(expired)

        # Act
        result = await reservation_service.get_expired_reservations()

        # Assert
        assert len(result) == 1
        assert result[0].id == expired.id

    @pytest.mark.asyncio
    async def test_expire_reservations_returns_count(
        self,
        reservation_service: ReservationService,
        mock_reservation_repo: MockReservationRepository,
        mock_cream_repo: MockCreamRepository,
    ):
        """expire_reservations should return the count of expired reservations."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=10)
        mock_cream_repo.add_cream(cream)

        expired1 = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=2,
            reserved_for=date.today() - timedelta(days=5),
        )
        expired2 = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=2,
            reserved_for=date.today() - timedelta(days=7),
        )
        active = Reservation(
            cream_id=cream.id,
            cream_name=cream.flavor_name,
            quantity_reserved=2,
            reserved_for=date.today(),
        )

        mock_reservation_repo.add_reservation(expired1)
        mock_reservation_repo.add_reservation(expired2)
        mock_reservation_repo.add_reservation(active)

        # Act
        count = await reservation_service.expire_reservations()

        # Assert
        assert count == 2

        # Both expired should be deactivated
        all_reservations = await mock_reservation_repo.get_by_cream_id(cream.id)
        inactive = [r for r in all_reservations if not r.is_active]
        assert len(inactive) == 2


class TestReservationServiceGetActive:
    """Tests for ReservationService.get_active_reservations."""

    @pytest.mark.asyncio
    async def test_get_active_reservations_returns_only_active(
        self,
        reservation_service: ReservationService,
        mock_reservation_repo: MockReservationRepository,
        sample_reservation: Reservation,
    ):
        """get_active_reservations should only return active reservations."""
        # Add an inactive one
        inactive = Reservation(
            cream_id=sample_reservation.cream_id,
            cream_name=sample_reservation.cream_name,
            quantity_reserved=2,
            reserved_for=date.today(),
            is_active=False,
        )
        mock_reservation_repo.add_reservation(inactive)

        # Act
        result = await reservation_service.get_active_reservations()

        # Assert
        assert len(result) == 1
        assert result[0].id == sample_reservation.id
        assert result[0].is_active is True
