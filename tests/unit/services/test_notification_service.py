"""
Tests for Notification Service — Phase 5.5

Validates NotificationService scenarios:
- test_low_stock_alert_not_sent_twice: The send_low_stock_alert method
  should only send one notification per day even when called multiple times.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.domain.entities.cream import Cream
from src.application.services.notification_service import NotificationService


class TestNotificationServiceLowStockAlert:
    """Tests for low-stock alert deduplication."""

    @pytest.fixture
    def notification_service(self) -> NotificationService:
        """Provides a fresh NotificationService instance."""
        return NotificationService()

    @pytest.fixture
    def low_stock_creams(self):
        """Provides a small list of low-stock creams."""
        return [
            Cream(flavor_name="Chocolate", quantity=1),
            Cream(flavor_name="Vainilla", quantity=2),
        ]

    async def test_low_stock_alert_not_sent_twice(
        self,
        notification_service: NotificationService,
        low_stock_creams,
    ):
        """
        test_low_stock_alert_not_sent_twice: When send_low_stock_alert is
        called multiple times on the same day, it should only send the email
        once. Subsequent calls within the same day should return False.
        """
        # Mock _send_email to track calls
        call_count = 0

        def track_send(subject: str, body: str) -> bool:
            nonlocal call_count
            call_count += 1
            return True

        with patch.object(
            notification_service,
            "_send_email",
            side_effect=track_send,
        ):
            # First call — should send (returns True)
            result1 = await notification_service.send_low_stock_alert(low_stock_creams)
            assert result1 is True
            assert call_count == 1

            # Second call — same day, should NOT send (returns False)
            result2 = await notification_service.send_low_stock_alert(low_stock_creams)
            assert result2 is False
            assert call_count == 1  # Still 1, not incremented

            # Third call — same day, should NOT send
            result3 = await notification_service.send_low_stock_alert(low_stock_creams)
            assert result3 is False
            assert call_count == 1

    async def test_low_stock_alert_sends_on_new_day(
        self,
        notification_service: NotificationService,
        low_stock_creams,
    ):
        """
        After crossing to a new day (simulated via last_notification_date
        reset), send_low_stock_alert should send again.
        """
        send_count = 0

        def track_send(subject: str, body: str) -> bool:
            nonlocal send_count
            send_count += 1
            return True

        with patch.object(
            notification_service,
            "_send_email",
            side_effect=track_send,
        ):
            # Simulate yesterday's notification
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            notification_service.last_notification_date = yesterday

            result = await notification_service.send_low_stock_alert(low_stock_creams)
            assert result is True
            assert send_count == 1

    async def test_low_stock_alert_returns_false_for_empty_list(
        self,
        notification_service: NotificationService,
    ):
        """send_low_stock_alert with no creams should return False."""
        result = await notification_service.send_low_stock_alert([])
        assert result is False

    async def test_low_stock_alert_body_contains_cream_info(
        self,
        notification_service: NotificationService,
        low_stock_creams,
    ):
        """The email body should list all low-stock creams with quantities."""
        captured_subject = None
        captured_body = None

        def capture_email(subject: str, body: str) -> bool:
            nonlocal captured_subject, captured_body
            captured_subject = subject
            captured_body = body
            return True

        with patch.object(
            notification_service,
            "_send_email",
            side_effect=capture_email,
        ):
            await notification_service.send_low_stock_alert(low_stock_creams)

        assert captured_subject is not None
        assert "Stock Bajo" in captured_subject
        assert "Chocolate" in captured_body
        assert "Vainilla" in captured_body
        assert "1" in captured_body
        assert "2" in captured_body
