"""
Tests for InventoryService

Covers cream CRUD, sale registration, and low-stock operations.
"""
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities.cream import Cream
from src.domain.entities.sale import Sale
from src.application.services.inventory_service import InventoryService


class TestInventoryServiceGetAll:
    """Tests for InventoryService.get_all_creams."""

    @pytest.mark.asyncio
    async def test_get_all_creams_returns_list_from_repo(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """get_all_creams should delegate to cream_repo.get_all."""
        # Arrange
        cream1 = Cream(flavor_name="Chocolate", quantity=10)
        cream2 = Cream(flavor_name="Vainilla", quantity=5)
        mock_cream_repo.add_cream(cream1)
        mock_cream_repo.add_cream(cream2)

        # Act
        result = await inventory_service.get_all_creams()

        # Assert
        assert len(result) == 2
        assert result[0].flavor_name == "Chocolate"
        assert result[1].flavor_name == "Vainilla"

    @pytest.mark.asyncio
    async def test_get_all_creams_returns_empty_when_no_creams(
        self,
        inventory_service: InventoryService,
    ):
        """get_all_creams should return empty list when no creams exist."""
        result = await inventory_service.get_all_creams()
        assert result == []


class TestInventoryServiceCreateCream:
    """Tests for InventoryService.create_cream."""

    @pytest.mark.asyncio
    async def test_create_cream_rejects_duplicate(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """create_cream should raise ValueError for duplicate flavor."""
        # Arrange - add existing cream
        existing = Cream(flavor_name="Chocolate", quantity=5)
        mock_cream_repo.add_cream(existing)

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe"):
            await inventory_service.create_cream("Chocolate")

    @pytest.mark.asyncio
    async def test_create_cream_succeeds_for_new_flavor(
        self,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """create_cream should succeed and call repo.create for new flavor."""
        # Arrange - explicitly set get_by_flavor_name to return None
        mock_cream_repo.get_by_flavor_name = AsyncMock(return_value=None)

        inventory_service = InventoryService(mock_cream_repo, mock_sale_repo)

        # Act
        result = await inventory_service.create_cream("Chocolate", quantity=10)

        # Assert
        assert result.flavor_name == "Chocolate"
        assert result.quantity == 10

    @pytest.mark.asyncio
    async def test_create_cream_flavor_name_case_insensitive(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """create_cream should reject duplicate regardless of case."""
        # Arrange
        existing = Cream(flavor_name="Chocolate", quantity=5)
        mock_cream_repo.add_cream(existing)

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe"):
            await inventory_service.create_cream("CHOCOLATE")


class TestInventoryServiceRegisterSale:
    """Tests for InventoryService.register_sale."""

    @pytest.mark.asyncio
    async def test_register_sale_fails_on_insufficient_stock(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """register_sale should raise ValueError when stock is insufficient."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=2)
        mock_cream_repo.add_cream(cream)

        # Act & Assert
        with pytest.raises(ValueError, match="insuficiente"):
            await inventory_service.register_sale(cream.id, quantity_sold=5)

    @pytest.mark.asyncio
    async def test_register_sale_succeeds_and_decrements_stock(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
        mock_sale_repo,
    ):
        """register_sale should succeed, decrement stock, and create sale."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=10)
        mock_cream_repo.add_cream(cream)

        # Act
        sale = await inventory_service.register_sale(cream.id, quantity_sold=3)

        # Assert
        assert sale.cream_id == cream.id
        assert sale.quantity_sold == 3
        assert sale.cream_name == "Chocolate"

        # Stock should be decremented
        updated_cream = await mock_cream_repo.get_by_id(cream.id)
        assert updated_cream.quantity == 7

    @pytest.mark.asyncio
    async def test_register_sale_fails_for_nonexistent_cream(
        self,
        inventory_service: InventoryService,
    ):
        """register_sale should raise ValueError for non-existent cream."""
        # Act & Assert
        with pytest.raises(ValueError, match="no encontrada"):
            await inventory_service.register_sale(uuid4(), quantity_sold=1)

    @pytest.mark.asyncio
    async def test_register_sale_exact_quantity(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """register_sale with exact stock should set quantity to zero."""
        # Arrange
        cream = Cream(flavor_name="Chocolate", quantity=3)
        mock_cream_repo.add_cream(cream)

        # Act
        await inventory_service.register_sale(cream.id, quantity_sold=3)

        # Assert
        updated_cream = await mock_cream_repo.get_by_id(cream.id)
        assert updated_cream.quantity == 0


class TestInventoryServiceGetLowStock:
    """Tests for InventoryService.get_low_stock_creams."""

    @pytest.mark.asyncio
    async def test_get_low_stock_creams_delegates_to_repo(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """get_low_stock_creams should delegate to cream_repo.get_low_stock."""
        # Arrange
        low1 = Cream(flavor_name="Chocolate", quantity=1)
        low2 = Cream(flavor_name="Vainilla", quantity=2)
        normal = Cream(flavor_name="Fresa", quantity=10)
        mock_cream_repo.add_cream(low1)
        mock_cream_repo.add_cream(low2)
        mock_cream_repo.add_cream(normal)

        # Act
        result = await inventory_service.get_low_stock_creams()

        # Assert
        assert len(result) == 2
        names = [c.flavor_name for c in result]
        assert "Chocolate" in names
        assert "Vainilla" in names
        assert "Fresa" not in names

    @pytest.mark.asyncio
    async def test_get_low_stock_creams_empty_when_all_stock_ok(
        self,
        inventory_service: InventoryService,
        mock_cream_repo,
    ):
        """get_low_stock_creams should return empty when no low-stock creams."""
        # Arrange
        cream1 = Cream(flavor_name="Chocolate", quantity=10)
        cream2 = Cream(flavor_name="Vainilla", quantity=5)
        mock_cream_repo.add_cream(cream1)
        mock_cream_repo.add_cream(cream2)

        # Act
        result = await inventory_service.get_low_stock_creams()

        # Assert
        assert result == []


class TestInventoryServiceGetCreamById:
    """Tests for InventoryService.get_cream_by_id."""

    @pytest.mark.asyncio
    async def test_get_cream_by_id_returns_cream(
        self,
        inventory_service: InventoryService,
        sample_cream: Cream,
    ):
        """get_cream_by_id should return the cream when it exists."""
        result = await inventory_service.get_cream_by_id(sample_cream.id)

        assert result is not None
        assert result.id == sample_cream.id
        assert result.flavor_name == "Chocolate"

    @pytest.mark.asyncio
    async def test_get_cream_by_id_returns_none_when_not_found(
        self,
        inventory_service: InventoryService,
    ):
        """get_cream_by_id should return None when cream does not exist."""
        result = await inventory_service.get_cream_by_id(uuid4())
        assert result is None
