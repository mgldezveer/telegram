"""Улучшенный обработчик ошибок с системой алертинга."""

import logging
import asyncio
import psutil
import traceback
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from telegram import Bot
from src.config import config
from src.cache import cache
from src.monitoring.realtime_error_detector import realtime_error_detector

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Категории ошибок."""
    GENERATION = "generation"
    PUBLISHING = "publishing"
    STORAGE = "storage"
    SCHEDULING = "scheduling"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    LLM = "llm"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Уровень важности алерта."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Контекст информации об ошибке."""
    category: ErrorCategory
    error: Exception
    timestamp: datetime
    component: str
    details: dict
    traceback_info: Optional[str] = None


@dataclass
class AlertConfig:
    """Конфигурация алерта."""
    severity: AlertSeverity
    message: str
    component: str
    details: dict


class EnhancedErrorHandler:
    """Улучшенный централизованный обработчик ошибок с системой алертинга."""
    
    def __init__(self, bot: Optional[Bot] = None, max_error_log_size: int = 1000):
        self.error_log: List[ErrorContext] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = 3
        self.resource_threshold = 0.8  # 80% порог использования
        self.max_error_log_size = max_error_log_size
        self.bot = bot
        self.admin_chat_ids = config.bot.admin_ids if hasattr(config, 'bot') and hasattr(config.bot, 'admin_ids') else []
        self._alert_cooldown: Dict[str, datetime] = {}  # Для предотвращения флуда алертов
        self._error_frequency: Dict[str, List[datetime]] = {}  # Отслеживание частоты ошибок
        self._cooldown_period = timedelta(minutes=5)  # 5 минут между алертами одного типа
    
    def _get_error_key(self, component: str, category: ErrorCategory) -> str:
        """Получить ключ для отслеживания ошибки.
        
        Args:
            component: Компонент системы
            category: Категория ошибки
            
        Returns:
            Ключ для отслеживания
        """
        return f"{component}:{category.value}"
    
    def _track_error_frequency(self, component: str, category: ErrorCategory):
        """Отследить частоту возникновения ошибки.
        
        Args:
            component: Компонент системы
            category: Категория ошибки
        """
        key = self._get_error_key(component, category)
        now = datetime.now()
        
        if key not in self._error_frequency:
            self._error_frequency[key] = []
        
        # Удалить старые записи (старше 1 минуты)
        self._error_frequency[key] = [
            timestamp for timestamp in self._error_frequency[key]
            if now - timestamp < timedelta(minutes=1)
        ]
        
        # Добавить текущую ошибку
        self._error_frequency[key].append(now)
    
    def _get_error_frequency(self, component: str, category: ErrorCategory) -> int:
        """Получить частоту ошибки за последнюю минуту.
        
        Args:
            component: Компонент системы
            category: Категория ошибки
            
        Returns:
            Количество ошибок за последнюю минуту
        """
        key = self._get_error_key(component, category)
        now = datetime.now()
        
        if key not in self._error_frequency:
            return 0
        
        # Удалить старые записи
        self._error_frequency[key] = [
            timestamp for timestamp in self._error_frequency[key]
            if now - timestamp < timedelta(minutes=1)
        ]
        
        return len(self._error_frequency[key])
    
    async def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        component: str,
        details: Optional[dict] = None
    ) -> bool:
        """Обработать ошибку с соответствующей стратегией восстановления.
        
        Args:
            error: Объект ошибки
            category: Категория ошибки
            component: Компонент системы
            details: Дополнительная информация
            
        Returns:
            True если была попытка восстановления
        """
        # Получить трейсбек ошибки
        traceback_info = traceback.format_exc()
        
        context = ErrorContext(
            category=category,
            error=error,
            timestamp=datetime.utcnow(),
            component=component,
            details=details or {},
            traceback_info=traceback_info
        )
        
        # Отслеживаем ошибку в системе детекции
        realtime_error_detector.track_exception(
            error,
            component,
            extra_data=details or {}
        )
        
        # Логировать ошибку
        await self._log_error(context)
        
        # Отследить частоту ошибки
        self._track_error_frequency(component, category)
        
        # Определить важность алерта на основе частоты и категории
        severity = self._determine_severity(context)
        
        # Отправить алерт если необходимо
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            await self._send_alert(AlertConfig(
                severity=severity,
                message=f"Ошибка в {component}: {str(error)}",
                component=component,
                details=details or {}
            ))
        
        # Попытаться восстановиться
        if await self._should_attempt_recovery(context):
            return await self._attempt_recovery(context)
        
        return False
    
    def _determine_severity(self, context: ErrorContext) -> AlertSeverity:
        """Определить важность алерта на основе контекста ошибки.
        
        Args:
            context: Контекст ошибки
            
        Returns:
            Уровень важности алерта
        """
        # Получить частоту ошибки за последнюю минуту
        frequency = self._get_error_frequency(context.component, context.category)
        
        # Критические категории ошибок
        if context.category in [ErrorCategory.DATABASE, ErrorCategory.LLM]:
            return AlertSeverity.CRITICAL
        
        # Ошибки, происходящие слишком часто
        if frequency >= 10:  # 10 и более ошибок в минуту
            return AlertSeverity.CRITICAL
        elif frequency >= 5:  # 5 и более ошибок в минуту
            return AlertSeverity.HIGH
        
        # Остальные ошибки
        if context.category in [ErrorCategory.NETWORK, ErrorCategory.STORAGE]:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    async def handle_critical_failure(
        self,
        error: Exception,
        component: str,
        recovery_func: Optional[Callable] = None
    ):
        """Обработать критический сбой с попыткой восстановления.
        
        Args:
            error: Объект ошибки
            component: Компонент системы
            recovery_func: Функция восстановления
        """
        logger.critical(f"Critical failure in {component}: {error}")
        
        # Отправить критический алерт
        await self._send_alert(AlertConfig(
            severity=AlertSeverity.CRITICAL,
            message=f"Критический сбой в {component}: {str(error)}",
            component=component,
            details={"traceback": traceback.format_exc()}
        ))
        
        if recovery_func:
            try:
                logger.info(f"Attempting graceful recovery for {component}")
                await recovery_func()
                logger.info(f"Recovery successful for {component}")
                
                # Отправить алерт об успешном восстановлении
                await self._send_alert(AlertConfig(
                    severity=AlertSeverity.LOW,
                    message=f"Успешное восстановление после сбоя в {component}",
                    component=component,
                    details={}
                ))
            except Exception as e:
                logger.error(f"Recovery failed for {component}: {e}")
                # Отправить алерт о неудачном восстановлении
                await self._send_alert(AlertConfig(
                    severity=AlertSeverity.CRITICAL,
                    message=f"Неудачное восстановление после сбоя в {component}: {str(e)}",
                    component=component,
                    details={"original_error": str(error), "recovery_error": str(e)}
                ))
        else:
            # Просто отправить алерт о критическом сбое
            await self._send_alert(AlertConfig(
                severity=AlertSeverity.CRITICAL,
                message=f"Критический сбой в {component} без возможности восстановления: {str(error)}",
                component=component,
                details={"traceback": traceback.format_exc()}
            ))
    
    async def check_resources(self) -> dict:
        """Проверить использование системных ресурсов.
        
        Returns:
            Словарь с информацией о ресурсах
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'timestamp': datetime.now().isoformat()
        }
        
        # Проверить, нужно ли ограничение
        if (cpu_percent > self.resource_threshold * 100 or
            memory.percent > self.resource_threshold * 100):
            logger.warning(f"High resource usage detected: {resources}")
            
            # Отправить алерт о высоком использовании ресурсов
            await self._send_alert(AlertConfig(
                severity=AlertSeverity.MEDIUM,
                message=f"Высокое использование ресурсов: CPU {cpu_percent}%, Memory {memory.percent}%",
                component="system",
                details=resources
            ))
            
            await self._throttle_operations()
        
        return resources
    
    async def graceful_shutdown(self, pending_operations: list):
        """Выполнить плавное завершение работы.
        
        Args:
            pending_operations: Список активных операций
        """
        logger.info("Initiating graceful shutdown")
        
        # Отправить алерт о начале завершения работы
        await self._send_alert(AlertConfig(
            severity=AlertSeverity.LOW,
            message="Начало плавного завершения работы бота",
            component="system",
            details={"pending_operations_count": len(pending_operations)}
        ))
        
        # Ждать завершения активных операций
        if pending_operations:
            logger.info(f"Waiting for {len(pending_operations)} pending operations")
            try:
                await asyncio.gather(*pending_operations, return_exceptions=True)
                logger.info("All pending operations completed")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        logger.info("Graceful shutdown complete")
    
    async def _log_error(self, context: ErrorContext):
        """Логировать ошибку с полным контекстом.
        
        Args:
            context: Контекст ошибки
        """
        # Добавить в лог ошибок
        self.error_log.append(context)
        
        # Ограничить размер лога
        if len(self.error_log) > self.max_error_log_size:
            self.error_log = self.error_log[-self.max_error_log_size:]
        
        logger.error(
            f"Error in {context.component} ({context.category.value}): "
            f"{type(context.error).__name__}: {context.error}",
            extra={
                'category': context.category.value,
                'component': context.component,
                'details': context.details,
                'timestamp': context.timestamp.isoformat(),
                'traceback': context.traceback_info
            }
        )
    
    async def _should_attempt_recovery(self, context: ErrorContext) -> bool:
        """Определить, следует ли пытаться восстановиться.
        
        Args:
            context: Контекст ошибки
            
        Returns:
            True если следует попытаться восстановиться
        """
        key = f"{context.component}:{context.category.value}"
        attempts = self.recovery_attempts.get(key, 0)
        
        # Не пытаться восстановиться если превышено максимальное количество попыток
        if attempts >= self.max_recovery_attempts:
            return False
        
        # Для критических ошибок ограничить количество попыток
        if context.category in [ErrorCategory.DATABASE, ErrorCategory.LLM]:
            return attempts < 2  # Только 2 попытки для критических ошибок
        
        return True
    
    async def _attempt_recovery(self, context: ErrorContext) -> bool:
        """Попытаться восстановиться после ошибки.
        
        Args:
            context: Контекст ошибки
            
        Returns:
            True если восстановление прошло успешно
        """
        key = f"{context.component}:{context.category.value}"
        self.recovery_attempts[key] = self.recovery_attempts.get(key, 0) + 1
        attempt_num = self.recovery_attempts[key]
        
        logger.info(f"Attempting recovery for {key} (attempt {attempt_num})")
        
        try:
            if context.category == ErrorCategory.NETWORK:
                # Ждать и повторить
                await asyncio.sleep(5 * attempt_num)  # Увеличивать задержку с каждой попыткой
                return True
            elif context.category == ErrorCategory.DATABASE:
                # Проверить соединение с базой данных
                from src.database.enhanced_db import enhanced_db
                health = await enhanced_db.health_check()
                if not health['healthy']:
                    logger.warning("Database connection unhealthy, attempting reconnection")
                    await enhanced_db.close()
                    await enhanced_db.initialize()
                return True
            elif context.category == ErrorCategory.CACHE:
                # Попытаться переподключиться к кэшу
                await cache.close()
                await cache.initialize()
                return True
            elif context.category == ErrorCategory.LLM:
                # Для ошибок LLM, попробовать перезагрузить менеджер
                from src.llm import get_llm_manager
                llm_manager = get_llm_manager()
                if llm_manager:
                    await llm_manager.reload()
                return True
            else:
                # Обычное восстановление
                await asyncio.sleep(2 * attempt_num)  # Увеличивать задержку с каждой попыткой
                return True
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False
    
    async def _throttle_operations(self):
        """Ограничить операции для снижения использования ресурсов."""
        logger.warning("Throttling operations due to high resource usage")
        
        # Здесь можно реализовать реальные механизмы ограничения
        # Например, уменьшение количества параллельных задач
        pass
    
    async def _cleanup_storage(self):
        """Очистить хранилище для освобождения места."""
        logger.info("Performing storage cleanup")
        
        # Здесь можно реализовать реальные механизмы очистки
        # Например, удаление старых логов или временных файлов
        pass
    
    async def _send_alert(self, alert_config: AlertConfig):
        """Отправить алерт администраторам.
        
        Args:
            alert_config: Конфигурация алерта
        """
        # Проверить, не прошло ли достаточно времени с последнего алерта этого типа
        cooldown_key = f"alert:{alert_config.component}:{alert_config.severity.value}"
        now = datetime.now()
        
        if cooldown_key in self._alert_cooldown:
            time_since_last = now - self._alert_cooldown[cooldown_key]
            if time_since_last < self._cooldown_period:
                # Пропустить алерт из-за ограничения по времени
                return
        
        # Обновить время последнего алерта
        self._alert_cooldown[cooldown_key] = now
        
        # Форматировать сообщение алерта
        severity_emoji = {
            AlertSeverity.LOW: "🟢",
            AlertSeverity.MEDIUM: "🟡",
            AlertSeverity.HIGH: "🟠",
            AlertSeverity.CRITICAL: "🔴"
        }
        
        message = (
            f"{severity_emoji[alert_config.severity]} <b>Алерт: {alert_config.severity.value.upper()}</b>\n\n"
            f"компонента: {alert_config.component}\n"
            f"Сообщение: {alert_config.message}\n\n"
        )
        
        if alert_config.details:
            message += "<b>Детали:</b>\n"
            for key, value in alert_config.details.items():
                message += f"• {key}: {value}\n"
        
        # Отправить алерт в Telegram если бот доступен
        if self.bot and self.admin_chat_ids:
            try:
                for admin_id in self.admin_chat_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=message,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.error(f"Failed to send alert to admin {admin_id}: {e}")
            except Exception as e:
                logger.error(f"Failed to send alerts: {e}")
        
        # Также логировать алерт
        logger.info(f"Alert sent: {alert_config.severity.value} - {alert_config.message}")
    
    async def get_error_stats(self) -> dict:
        """Получить статистику по ошибкам.
        
        Returns:
            Словарь со статистикой
        """
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        
        # Подсчитать ошибки за последний час
        recent_errors = [
            error for error in self.error_log
            if error.timestamp >= last_hour
        ]
        
        # Подсчитать ошибки по категориям
        category_counts = {}
        for error in recent_errors:
            cat = error.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Подсчитать частоту ошибок
        total_errors = len(recent_errors)
        
        return {
            'total_errors_last_hour': total_errors,
            'error_frequency_by_category': category_counts,
            'total_logged_errors': len(self.error_log),
            'recovery_attempts': dict(self.recovery_attempts),
            'error_frequency_details': {
                key: len(timestamps) 
                for key, timestamps in self._error_frequency.items()
                if now - max(timestamps) < timedelta(minutes=1)  # Только за последнюю минуту
            }
        }
    
    async def clear_error_log(self):
        """Очистить лог ошибок."""
        self.error_log.clear()
        self.recovery_attempts.clear()
        self._error_frequency.clear()
        logger.info("Error log cleared")