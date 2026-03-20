"""
Tests for Cream Entity

Covers creation validation, add_stock, remove_stock, and is_low_stock.
"""
from datetime import datetime
from uuid import uuid4

import pytest

from src.domain.entities.cream import Cream


class TestCreamCreation:
    """Tests for Cream entity creation."""

    def test_cream_creation_with_valid_data(self):
        """Cream with valid flavor_name and quantity should be created successfully."""
        cream = Cream(flavor_name="Chocolate", quantity=10)

        assert cream.flavor_name == "Chocolate"
        assert cream.quantity == 10
        assert cream.id is not None
        assert isinstance(cream.id, type(uuid4()))

    def test_cream_creation_with_zero_quantity(self):
        """Cream with zero quantity is valid."""
        cream = Cream(flavor_name="Vainilla", quantity=0)

        assert cream.quantity == 0
        assert cream.flavor_name == "Vainilla"

    def test_cream_creation_with_empty_flavor_name_raises(self):
        """Cream with empty flavor_name should raise ValueError."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            Cream(flavor_name="", quantity=5)

    def test_cream_creation_with_whitespace_only_flavor_name_raises(self):
        """Cream with whitespace-only flavor_name should raise ValueError."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            Cream(flavor_name="   ", quantity=5)

    def test_cream_creation_with_negative_quantity_raises(self):
        """Cream with negative quantity should raise ValueError."""
        with pytest.raises(ValueError, match="negativa"):
            Cream(flavor_name="Chocolate", quantity=-5)

    def test_cream_flavor_name_is_stripped(self):
        """Cream flavor_name should be stripped of whitespace."""
        cream = Cream(flavor_name="  Chocolate Blanco  ", quantity=3)

        assert cream.flavor_name == "Chocolate Blanco"


class TestCreamAddStock:
    """Tests for Cream.add_stock method."""

    def test_add_stock_with_positive_amount_increases_quantity(self):
        """add_stock with positive amount should increase quantity."""
        cream = Cream(flavor_name="Chocolate", quantity=10)

        cream.add_stock(5)

        assert cream.quantity == 15

    def test_add_stock_with_zero_amount_raises(self):
        """add_stock with zero amount should raise ValueError."""
        cream = Cream(flavor_name="Chocolate", quantity=10)

        with pytest.raises(ValueError, match="mayor a 0"):
            cream.add_stock(0)

    def test_add_stock_with_negative_amount_raises(self):
        """add_stock with negative amount should raise ValueError."""
        cream = Cream(flavor_name="Chocolate", quantity=10)

        with pytest.raises(ValueError, match="mayor a 0"):
            cream.add_stock(-3)

    def test_add_stock_updates_quantity(self):
        """add_stock should update the quantity correctly."""
        cream = Cream(flavor_name="Chocolate", quantity=10)
        cream.add_stock(1)
        assert cream.quantity == 11


class TestCreamRemoveStock:
    """Tests for Cream.remove_stock method."""

    def test_remove_stock_with_sufficient_stock_decreases_quantity(self):
        """remove_stock with sufficient quantity should decrease stock."""
        cream = Cream(flavor_name="Chocolate", quantity=10)

        cream.remove_stock(3)

        assert cream.quantity == 7

    def test_remove_stock_exact_quantity(self):
        """remove_stock with exact quantity should set quantity to zero."""
        cream = Cream(flavor_name="Chocolate", quantity=5)

        cream.remove_stock(5)

        assert cream.quantity == 0

    def test_remove_stock_with_insufficient_quantity_raises(self):
        """remove_stock exceeding stock should raise ValueError."""
        cream = Cream(flavor_name="Chocolate", quantity=5)

        with pytest.raises(ValueError, match="suficiente stock"):
            cream.remove_stock(10)

    def test_remove_stock_with_zero_amount_raises(self):
        """remove_stock with zero should raise ValueError."""
        cream = Cream(flavor_name="Chocolate", quantity=10)

        with pytest.raises(ValueError, match="mayor a 0"):
            cream.remove_stock(0)

    def test_remove_stock_with_negative_amount_raises(self):
        """remove_stock with negative amount should raise ValueError."""
        cream = Cream(flavor_name="Chocolate", quantity=10)

        with pytest.raises(ValueError, match="mayor a 0"):
            cream.remove_stock(-2)


class TestCreamIsLowStock:
    """Tests for Cream.is_low_stock method."""

    def test_is_low_stock_below_threshold_returns_true(self):
        """is_low_stock with quantity below threshold returns True."""
        cream = Cream(flavor_name="Chocolate", quantity=2)

        assert cream.is_low_stock(threshold=3) is True

    def test_is_low_stock_at_threshold_returns_true(self):
        """is_low_stock with quantity equal to threshold returns True."""
        cream = Cream(flavor_name="Chocolate", quantity=3)

        assert cream.is_low_stock(threshold=3) is True

    def test_is_low_stock_above_threshold_returns_false(self):
        """is_low_stock with quantity above threshold returns False."""
        cream = Cream(flavor_name="Chocolate", quantity=5)

        assert cream.is_low_stock(threshold=3) is False

    def test_is_low_stock_with_zero_quantity(self):
        """is_low_stock with zero quantity returns True."""
        cream = Cream(flavor_name="Chocolate", quantity=0)

        assert cream.is_low_stock(threshold=3) is True

    def test_is_low_stock_default_threshold(self):
        """is_low_stock uses default threshold of 3."""
        cream = Cream(flavor_name="Chocolate", quantity=3)

        # Default threshold is 3, so quantity == threshold should be True
        assert cream.is_low_stock() is True

        cream.quantity = 4
        assert cream.is_low_stock() is False
