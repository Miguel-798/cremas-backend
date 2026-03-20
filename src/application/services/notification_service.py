"""
Notification Service - Application Layer

Servicio para enviar notificaciones de alertas via Gmail.
"""
from datetime import datetime, timedelta
from typing import List
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.domain import Cream
from src.infrastructure.config import settings
from src.infrastructure.logging import get_logger

log = get_logger(__name__)


class NotificationService:
    """Servicio para enviar notificaciones por Gmail."""
    
    def __init__(self):
        self.enabled = bool(
            settings.gmail_client_id 
            and settings.gmail_client_secret 
            and settings.gmail_refresh_token
        )
        self.from_email = settings.gmail_from_email
        self.to_email = settings.gmail_to_email
        self.last_notification_date: str | None = None
    
    def _get_credentials(self) -> Credentials:
        """Obtener credenciales de Gmail API."""
        return Credentials(
            token=None,
            refresh_token=settings.gmail_refresh_token,
            client_id=settings.gmail_client_id,
            client_secret=settings.gmail_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )
    
    def _send_email(self, subject: str, body: str) -> bool:
        """
        Enviar email usando Gmail API.
        
        Returns:
            True si se envió correctamente, False si falló
        """
        if not self.enabled:
            log.debug("notification.disabled", subject=subject)
            return False
        
        try:
            credentials = self._get_credentials()
            service = build("gmail", "v1", credentials=credentials)
            
            message = f"From: {self.from_email}\n"
            message += f"To: {self.to_email}\n"
            message += f"Subject: {subject}\n\n"
            message += body
            
            encoded_message = {"raw": message}
            
            service.users().messages().send(
                userId="me",
                body=encoded_message
            ).execute()
            
            log.info("notification.sent", subject=subject)
            return True
            
        except Exception as e:
            log.error("notification.send_failed", subject=subject, error=str(e))
            return False
    
    async def send_low_stock_alert(self, creams: List[Cream]) -> bool:
        """
        Enviar alerta de stock bajo.
        
        Rules:
        - Solo enviar una vez por día
        - Solo enviar si hay cremas con stock bajo
        """
        if not creams:
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Evitar spam - solo una notificación por día
        if self.last_notification_date == today:
            log.debug("notification.already_sent_today")
            return False
        
        self.last_notification_date = today
        
        # Construir mensaje
        subject = "⚠️ Alerta: Stock Bajo de Cremas"
        
        body = "Las siguientes cremas tienen stock bajo:\n\n"
        for cream in creams:
            body += f"• {cream.flavor_name}: {cream.quantity} unidades\n"
        
        body += f"\nUmbral de alerta: {settings.low_stock_threshold} unidades\n"
        body += f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self._send_email(subject, body)
    
    async def send_daily_check(self, all_creams: List[Cream]) -> bool:
        """
        Enviar verificación diaria del inventario.
        
        Envía un resumen aunque no haya alertas.
        """
        low_stock = [c for c in all_creams if c.is_low_stock(settings.low_stock_threshold)]
        
        if low_stock:
            return await self.send_low_stock_alert(low_stock)
        
        # Solo enviar resumen si hay pocas cremas (para no spamear)
        if len(all_creams) <= 3 and all_creams:
            subject = "📊 Resumen Diario de Inventario"
            body = f"Inventario OK. Total de cremas: {len(all_creams)}\n\n"
            for cream in all_creams:
                body += f"• {cream.flavor_name}: {cream.quantity} unidades\n"
            body += f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return self._send_email(subject, body)
        
        return False
