"""
Tests for Reservation Entity

Covers creation validation, is_expired, activate, and deactivate.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from src.domain.entities.reservation import Reservation


class TestReservationCreation:
    """Tests for Reservation entity creation."""

    def test_reservation_creation_with_valid_data(self):
        """Reservation with valid data should be created successfully."""
        reserved_for = date.today()
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Vainilla",
            quantity_reserved=3,
            reserved_for=reserved_for,
        )

        assert reservation.cream_name == "Vainilla"
        assert reservation.quantity_reserved == 3
        assert reservation.reserved_for == reserved_for
        assert reservation.is_active is True
        assert reservation.id is not None

    def test_reservation_creation_with_customer_name(self):
        """Reservation with optional customer_name should store it."""
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=2,
            reserved_for=date.today(),
            customer_name="Juan Pérez",
        )

        assert reservation.customer_name == "Juan Pérez"

    def test_reservation_creation_with_invalid_quantity_raises(self):
        """Reservation with quantity <= 0 should raise ValueError."""
        with pytest.raises(ValueError, match="mayor a 0"):
            Reservation(
                cream_id=uuid4(),
                cream_name="Chocolate",
                quantity_reserved=0,
                reserved_for=date.today(),
            )

    def test_reservation_creation_with_negative_quantity_raises(self):
        """Reservation with negative quantity should raise ValueError."""
        with pytest.raises(ValueError, match="mayor a 0"):
            Reservation(
                cream_id=uuid4(),
                cream_name="Chocolate",
                quantity_reserved=-3,
                reserved_for=date.today(),
            )

    def test_reservation_creation_without_cream_name_raises(self):
        """Reservation without cream_name should raise ValueError."""
        with pytest.raises(ValueError, match="sabor es requerido"):
            Reservation(
                cream_id=uuid4(),
                cream_name="",
                quantity_reserved=3,
                reserved_for=date.today(),
            )

    def test_reservation_customer_name_is_stripped(self):
        """Reservation customer_name should be stripped."""
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=2,
            reserved_for=date.today(),
            customer_name="  Juan Pérez  ",
        )

        assert reservation.customer_name == "Juan Pérez"


class TestReservationIsExpired:
    """Tests for Reservation.is_expired method."""

    def test_is_expired_within_expiry_days_returns_false(self):
        """is_expired returns False when reserved_for is within expiry period."""
        reserved_for = date.today()
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=3,
            reserved_for=reserved_for,
        )

        # Today is within expiry_days=2 of reserved_for
        assert reservation.is_expired(expiry_days=2) is False

    def test_is_expired_past_expiry_days_returns_true(self):
        """is_expired returns True when past the expiry period."""
        reserved_for = date.today() - timedelta(days=5)
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=3,
            reserved_for=reserved_for,
        )

        # Today (today - 5 days) > (today - 5 days + 2 days)
        assert reservation.is_expired(expiry_days=2) is True

    def test_is_expired_exactly_on_expiry_boundary_returns_true(self):
        """is_expired returns True when exactly on the expiry boundary."""
        # reserved_for + expiry_days = yesterday, so today > boundary
        reserved_for = date.today() - timedelta(days=3)
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=3,
            reserved_for=reserved_for,
        )

        assert reservation.is_expired(expiry_days=2) is True

    def test_is_expired_with_future_date_returns_false(self):
        """is_expired returns False for future reserved_for dates."""
        reserved_for = date.today() + timedelta(days=1)
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=3,
            reserved_for=reserved_for,
        )

        assert reservation.is_expired(expiry_days=2) is False


class TestReservationActivateDeactivate:
    """Tests for Reservation activate and deactivate methods."""

    def test_deactivate_marks_reservation_inactive(self):
        """deactivate should set is_active to False."""
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=3,
            reserved_for=date.today(),
            is_active=True,
        )

        reservation.deactivate()

        assert reservation.is_active is False

    def test_activate_marks_reservation_active(self):
        """activate should set is_active to True."""
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=3,
            reserved_for=date.today(),
            is_active=False,
        )

        reservation.activate()

        assert reservation.is_active is True

    def test_activate_toggle_workflow(self):
        """Test full activate -> deactivate -> activate workflow."""
        reservation = Reservation(
            cream_id=uuid4(),
            cream_name="Chocolate",
            quantity_reserved=3,
            reserved_for=date.today(),
        )

        # Initially active
        assert reservation.is_active is True

        # Deactivate
        reservation.deactivate()
        assert reservation.is_active is False

        # Reactivate
        reservation.activate()
        assert reservation.is_active is True
