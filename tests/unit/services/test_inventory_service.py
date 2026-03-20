"""
Tests for Inventory Service — Phase 5.4

Validates InventoryService edge cases:
- test_sale_with_insufficient_stock_raises: register_sale should raise
  ValueError when quantity_sold > available stock
- test_create_cream_validates: create_cream should validate flavor_name
  and reject empty/whitespace names
"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities.cream import Cream
from src.application.services.inventory_service import InventoryService


class TestInventoryServiceSaleValidation:
    """Tests for sale validation in InventoryService."""

    async def test_sale_with_insufficient_stock_raises(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """
        test_sale_with_insufficient_stock_raises: Attempting to sell more
        units than are available should raise ValueError with a message
        indicating insufficient stock.
        """
        # Arrange — a cream with quantity of 2
        cream = Cream(flavor_name="Vainilla", quantity=2)
        mock_cream_repo.add_cream(cream)

        # Act & Assert — trying to sell 5 should raise
        with pytest.raises(ValueError, match="[Ii]nsuficiente|[Ss]tock"):
            await inventory_service.register_sale(cream.id, quantity_sold=5)

    async def test_sale_with_exactly_available_stock_succeeds(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """Selling exactly the available quantity should succeed."""
        cream = Cream(flavor_name="Fresa", quantity=5)
        mock_cream_repo.add_cream(cream)

        sale = await inventory_service.register_sale(cream.id, quantity_sold=5)

        assert sale.quantity_sold == 5
        updated_cream = await mock_cream_repo.get_by_id(cream.id)
        assert updated_cream.quantity == 0


class TestInventoryServiceCreateCreamValidation:
    """Tests for create_cream validation in InventoryService."""

    async def test_create_cream_validates_empty_flavor_name(
        self,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """
        test_create_cream_validates: create_cream should validate that
        flavor_name is not empty or whitespace and raise ValueError.
        """
        mock_cream_repo.get_by_flavor_name = AsyncMock(return_value=None)
        service = InventoryService(mock_cream_repo, mock_sale_repo)

        # Empty string should raise
        with pytest.raises(ValueError):
            await service.create_cream("")

    async def test_create_cream_validates_whitespace_only_name(
        self,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """Whitespace-only flavor names should raise ValueError."""
        mock_cream_repo.get_by_flavor_name = AsyncMock(return_value=None)
        service = InventoryService(mock_cream_repo, mock_sale_repo)

        with pytest.raises(ValueError):
            await service.create_cream("   ")

    async def test_create_cream_validates_negative_quantity(
        self,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """
        create_cream with negative quantity should raise ValueError
        (validation flows through Cream entity constructor).
        """
        mock_cream_repo.get_by_flavor_name = AsyncMock(return_value=None)
        service = InventoryService(mock_cream_repo, mock_sale_repo)

        with pytest.raises(ValueError):
            await service.create_cream("Chocolate", quantity=-1)

    async def test_create_cream_rejects_duplicate(
        self,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """create_cream should reject a flavor that already exists."""
        existing = Cream(flavor_name="Chocolate", quantity=5)
        mock_cream_repo.add_cream(existing)

        service = InventoryService(mock_cream_repo, mock_sale_repo)

        with pytest.raises(ValueError, match="Ya existe"):
            await service.create_cream("Chocolate")

    async def test_create_cream_rejects_duplicate_case_insensitive(
        self,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """create_cream should reject duplicate regardless of case."""
        existing = Cream(flavor_name="Chocolate", quantity=5)
        mock_cream_repo.add_cream(existing)

        service = InventoryService(mock_cream_repo, mock_sale_repo)

        with pytest.raises(ValueError, match="Ya existe"):
            await service.create_cream("CHOCOLATE")

    async def test_create_cream_strips_flavor_name(
        self,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """create_cream should strip leading/trailing whitespace from flavor_name."""
        mock_cream_repo.get_by_flavor_name = AsyncMock(return_value=None)
        service = InventoryService(mock_cream_repo, mock_sale_repo)

        cream = await service.create_cream("  Chocolate Blanco  ", quantity=10)

        assert cream.flavor_name == "Chocolate Blanco"
