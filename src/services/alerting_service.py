"""Alerting service for critical events and errors."""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels."""
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class Alert:
    """Alert data structure."""
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    component: str
    details: Dict[str, Any]
    correlation_id: Optional[str] = None


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str
    severity: AlertSeverity
    channels: List[AlertChannel]
    cooldown_minutes: int = 5
    enabled: bool = True


class AlertingService:
    """Service for sending alerts about critical events."""
    
    def __init__(
        self,
        telegram_bot_token: Optional[str] = None,
        admin_chat_ids: Optional[List[int]] = None,
        webhook_url: Optional[str] = None
    ):
        """Initialize alerting service.
        
        Args:
            telegram_bot_token: Telegram bot token for sending alerts
            admin_chat_ids: List of admin chat IDs
            webhook_url: Webhook URL for external alerting systems
        """
        self.telegram_bot_token = telegram_bot_token
        self.admin_chat_ids = admin_chat_ids or []
        self.webhook_url = webhook_url
        
        # Alert history for cooldown
        self.alert_history: Dict[str, datetime] = {}
        
        # Alert rules
        self.rules: List[AlertRule] = self._default_rules()
        
        # Alert queue
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
    
    def _default_rules(self) -> List[AlertRule]:
        """Get default alert rules."""
        return [
            AlertRule(
                name="database_connection_lost",
                condition="database.connection == False",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.TELEGRAM, AlertChannel.LOG],
                cooldown_minutes=5
            ),
            AlertRule(
                name="high_error_rate",
                condition="error_rate > 10%",
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.TELEGRAM, AlertChannel.LOG],
                cooldown_minutes=10
            ),
            AlertRule(
                name="memory_usage_high",
                condition="memory_usage > 90%",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG],
                cooldown_minutes=15
            ),
            AlertRule(
                name="api_rate_limit",
                condition="rate_limit_hit == True",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG],
                cooldown_minutes=5
            )
        ]
    
    async def start(self):
        """Start alert worker."""
        if not self._worker_task:
            self._worker_task = asyncio.create_task(self._alert_worker())
            logger.info("Alert worker started")
    
    async def stop(self):
        """Stop alert worker."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Alert worker stopped")
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        component: str,
        details: Optional[Dict[str, Any]] = None,
        channels: Optional[List[AlertChannel]] = None,
        correlation_id: Optional[str] = None
    ):
        """Send alert through configured channels.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            component: Component that triggered alert
            details: Additional details
            channels: Channels to send alert to (default: all)
            correlation_id: Correlation ID for tracing
        """
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.utcnow(),
            component=component,
            details=details or {},
            correlation_id=correlation_id
        )
        
        # Check cooldown
        alert_key = f"{component}:{title}"
        if alert_key in self.alert_history:
            last_alert = self.alert_history[alert_key]
            if datetime.utcnow() - last_alert < timedelta(minutes=5):
                logger.debug(f"Alert {alert_key} in cooldown, skipping")
                return
        
        # Update history
        self.alert_history[alert_key] = datetime.utcnow()
        
        # Queue alert for processing
        await self.alert_queue.put((alert, channels))
        
        logger.info(
            f"Alert queued: {title}",
            extra={
                'severity': severity.value,
                'component': component,
                'correlation_id': correlation_id
            }
        )
    
    async def _alert_worker(self):
        """Background worker for processing alerts."""
        while True:
            try:
                alert, channels = await self.alert_queue.get()
                await self._process_alert(alert, channels)
                self.alert_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert worker: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_alert(
        self,
        alert: Alert,
        channels: Optional[List[AlertChannel]]
    ):
        """Process and send alert through channels."""
        channels = channels or [AlertChannel.TELEGRAM, AlertChannel.LOG]
        
        # Send through each channel
        tasks = []
        for channel in channels:
            if channel == AlertChannel.TELEGRAM:
                tasks.append(self._send_telegram_alert(alert))
            elif channel == AlertChannel.EMAIL:
                tasks.append(self._send_email_alert(alert))
            elif channel == AlertChannel.WEBHOOK:
                tasks.append(self._send_webhook_alert(alert))
            elif channel == AlertChannel.LOG:
                self._log_alert(alert)
        
        # Send all alerts concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Failed to send alert: {result}")
    
    async def _send_telegram_alert(self, alert: Alert):
        """Send alert via Telegram."""
        if not self.telegram_bot_token or not self.admin_chat_ids:
            logger.warning("Telegram alerting not configured")
            return
        
        # Format message
        emoji = self._get_severity_emoji(alert.severity)
        text = (
            f"{emoji} <b>{alert.title}</b>\n\n"
            f"<b>Severity:</b> {alert.severity.value.upper()}\n"
            f"<b>Component:</b> {alert.component}\n"
            f"<b>Time:</b> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            f"{alert.message}\n\n"
        )
        
        if alert.details:
            text += "<b>Details:</b>\n"
            for key, value in alert.details.items():
                text += f"• {key}: {value}\n"
        
        if alert.correlation_id:
            text += f"\n<code>ID: {alert.correlation_id}</code>"
        
        # Send to all admin chats
        async with aiohttp.ClientSession() as session:
            for chat_id in self.admin_chat_ids:
                try:
                    url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                    data = {
                        'chat_id': chat_id,
                        'text': text,
                        'parse_mode': 'HTML'
                    }
                    
                    async with session.post(url, json=data) as response:
                        if response.status != 200:
                            logger.error(
                                f"Failed to send Telegram alert to {chat_id}: "
                                f"{response.status}"
                            )
                except Exception as e:
                    logger.error(f"Error sending Telegram alert: {e}")
    
    async def _send_email_alert(self, alert: Alert):
        """Send alert via email."""
        # TODO: Implement email alerting
        logger.info(f"Email alert: {alert.title}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook."""
        if not self.webhook_url:
            logger.warning("Webhook alerting not configured")
            return
        
        payload = {
            'title': alert.title,
            'message': alert.message,
            'severity': alert.severity.value,
            'component': alert.component,
            'timestamp': alert.timestamp.isoformat(),
            'details': alert.details,
            'correlation_id': alert.correlation_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"Webhook alert failed: {response.status}"
                        )
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    def _log_alert(self, alert: Alert):
        """Log alert to logging system."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }[alert.severity]
        
        logger.log(
            log_level,
            f"ALERT: {alert.title} - {alert.message}",
            extra={
                'alert_severity': alert.severity.value,
                'alert_component': alert.component,
                'alert_details': alert.details,
                'correlation_id': alert.correlation_id
            }
        )
    
    def _get_severity_emoji(self, severity: AlertSeverity) -> str:
        """Get emoji for severity level."""
        return {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }[severity]
    
    async def alert_database_error(self, error: Exception, details: Dict[str, Any]):
        """Send database error alert."""
        await self.send_alert(
            title="Database Error",
            message=f"Database operation failed: {str(error)}",
            severity=AlertSeverity.CRITICAL,
            component="database",
            details=details
        )
    
    async def alert_api_error(self, api_name: str, error: Exception):
        """Send API error alert."""
        await self.send_alert(
            title=f"{api_name} API Error",
            message=f"API request failed: {str(error)}",
            severity=AlertSeverity.ERROR,
            component="api",
            details={'api': api_name, 'error_type': type(error).__name__}
        )
    
    async def alert_high_memory(self, memory_percent: float):
        """Send high memory usage alert."""
        await self.send_alert(
            title="High Memory Usage",
            message=f"Memory usage is at {memory_percent:.1f}%",
            severity=AlertSeverity.WARNING,
            component="system",
            details={'memory_percent': memory_percent}
        )
    
    async def alert_rate_limit(self, service: str, limit: int):
        """Send rate limit alert."""
        await self.send_alert(
            title="Rate Limit Reached",
            message=f"Rate limit reached for {service}",
            severity=AlertSeverity.WARNING,
            component="rate_limiter",
            details={'service': service, 'limit': limit}
        )
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alerting statistics."""
        return {
            'total_alerts': len(self.alert_history),
            'queue_size': self.alert_queue.qsize(),
            'worker_running': self._worker_task is not None and not self._worker_task.done(),
            'configured_channels': {
                'telegram': bool(self.telegram_bot_token and self.admin_chat_ids),
                'webhook': bool(self.webhook_url)
            }
        }


# Global alerting service instance
_alerting_service: Optional[AlertingService] = None


def get_alerting_service() -> AlertingService:
    """Get global alerting service instance."""
    global _alerting_service
    if _alerting_service is None:
        from src.config import config
        _alerting_service = AlertingService(
            telegram_bot_token=config.bot.token,
            admin_chat_ids=config.bot.admin_ids
        )
    return _alerting_service


async def send_alert(
    title: str,
    message: str,
    severity: AlertSeverity,
    component: str,
    **kwargs
):
    """Convenience function to send alert."""
    service = get_alerting_service()
    await service.send_alert(title, message, severity, component, **kwargs)
