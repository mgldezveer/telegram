"""Система обнаружения ошибок в реальном времени для Telegram-бота."""

import logging
import time
import asyncio
import traceback
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict, deque

from src.monitoring.enhanced_monitoring import EnhancedMonitoring, enhanced_monitoring
from src.logging_config_improved import get_logger


class ErrorPriority(Enum):
    """Приоритеты ошибок."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorType(Enum):
    """Типы ошибок."""
    EXCEPTION = "exception"
    PERFORMANCE = "performance"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class AnomalyType(Enum):
    """Типы аномалий производительности."""
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNUSUAL_TRAFFIC = "unusual_traffic"
    FAILED_CONNECTIONS = "failed_connections"


@dataclass
class ErrorEvent:
    """Событие ошибки."""
    timestamp: datetime
    error_type: ErrorType
    priority: ErrorPriority
    component: str
    message: str
    exception: Optional[Exception] = None
    traceback_info: Optional[str] = None
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    command: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceAnomaly:
    """Событие аномалии производительности."""
    timestamp: datetime
    anomaly_type: AnomalyType
    component: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: ErrorPriority
    description: str
    extra_data: Optional[Dict[str, Any]] = None


class RealtimeErrorDetector:
    """Система обнаружения ошибок в реальном времени для Telegram-бота."""
    
    def __init__(self, 
                 anomaly_detection_window: int = 60,  # в секундах
                 high_error_rate_threshold: float = 0.1,  # 10% ошибок
                 high_latency_threshold: float = 5.0,  # 5 секунд
                 resource_threshold: float = 0.8,  # 80% ресурсов
                 notification_callback: Optional[Callable[[ErrorEvent], None]] = None):
        """
        Инициализация системы обнаружения ошибок.
        
        Args:
            anomaly_detection_window: Окно для анализа аномалий (в секундах)
            high_error_rate_threshold: Порог для высокой частоты ошибок
            high_latency_threshold: Порог для высокой задержки (в секундах)
            resource_threshold: Порог для истощения ресурсов (0-1)
            notification_callback: Коллбэк для уведомлений об ошибках
        """
        self.logger = get_logger(__name__)
        self.enhanced_monitoring = enhanced_monitoring
        self.anomaly_detection_window = anomaly_detection_window
        self.high_error_rate_threshold = high_error_rate_threshold
        self.high_latency_threshold = high_latency_threshold
        self.resource_threshold = resource_threshold
        self.notification_callback = notification_callback
        
        # Буферы для анализа аномалий
        self.error_buffer = deque(maxlen=1000)  # буфер ошибок
        self.performance_buffer = deque(maxlen=1000)  # буфер метрик производительности
        self.request_times = defaultdict(lambda: deque(maxlen=100))  # времена запросов по компонентам
        
        # Статистика для анализа
        self.component_error_counts = defaultdict(lambda: defaultdict(int))  # счетчик ошибок по компонентам и типам
        self.component_request_counts = defaultdict(int)  # счетчик запросов по компонентам
        self.component_error_timers = defaultdict(lambda: deque(maxlen=1000))  # таймеры ошибок
        
        # Асинхронные задачи
        self._running = False
        self._anomaly_detection_task: Optional[asyncio.Task] = None
        
        self.logger.info("Realtime Error Detector initialized")
    
    async def start(self):
        """Запустить систему обнаружения ошибок."""
        if self._running:
            return
        
        self._running = True
        self._anomaly_detection_task = asyncio.create_task(self._anomaly_detection_loop())
        self.logger.info("Realtime Error Detector started")
    
    async def stop(self):
        """Остановить систему обнаружения ошибок."""
        self._running = False
        if self._anomaly_detection_task:
            self._anomaly_detection_task.cancel()
            try:
                await self._anomaly_detection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Realtime Error Detector stopped")
    
    async def _anomaly_detection_loop(self):
        """Цикл обнаружения аномалий."""
        while self._running:
            try:
                await self._detect_performance_anomalies()
                await asyncio.sleep(10)  # проверять каждые 10 секунд
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in anomaly detection loop: {e}")
                await asyncio.sleep(10)
    
    def track_exception(self, 
                       exception: Exception, 
                       component: str, 
                       user_id: Optional[str] = None,
                       chat_id: Optional[str] = None,
                       command: Optional[str] = None,
                       extra_data: Optional[Dict[str, Any]] = None) -> ErrorEvent:
        """
        Отследить исключение в обработчиках бота.
        
        Args:
            exception: Исключение
            component: Компонент, где произошло исключение
            user_id: ID пользователя
            chat_id: ID чата
            command: Команда, вызвавшая исключение
            extra_data: Дополнительные данные
            
        Returns:
            ErrorEvent: Событие ошибки
        """
        error_type, priority = self._classify_exception(exception)
        
        error_event = ErrorEvent(
            timestamp=datetime.utcnow(),
            error_type=error_type,
            priority=priority,
            component=component,
            message=str(exception),
            exception=exception,
            traceback_info=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id,
            command=command,
            extra_data=extra_data
        )
        
        # Добавить в буфер
        self.error_buffer.append(error_event)
        
        # Обновить статистику
        self.component_error_counts[component][error_type.value] += 1
        self.component_error_timers[component].append(time.time())
        
        # Отправить уведомление
        self._send_notification(error_event)
        
        # Записать в лог
        self._log_error_event(error_event)
        
        # Отследить в системе мониторинга
        self.enhanced_monitoring.track_error(
            component=component,
            error_type=error_type.value,
            severity=priority.value,
            error_category='exception'
        )
        
        return error_event
    
    def track_performance_anomaly(self, 
                                 anomaly_type: AnomalyType,
                                 component: str,
                                 metric_name: str,
                                 current_value: float,
                                 threshold_value: float,
                                 description: str,
                                 extra_data: Optional[Dict[str, Any]] = None) -> PerformanceAnomaly:
        """
        Отследить аномалию в производительности.
        
        Args:
            anomaly_type: Тип аномалии
            component: Компонент системы
            metric_name: Имя метрики
            current_value: Текущее значение
            threshold_value: Пороговое значение
            description: Описание аномалии
            extra_data: Дополнительные данные
            
        Returns:
            PerformanceAnomaly: Событие аномалии
        """
        severity = self._determine_anomaly_severity(current_value, threshold_value, anomaly_type)
        
        anomaly_event = PerformanceAnomaly(
            timestamp=datetime.utcnow(),
            anomaly_type=anomaly_type,
            component=component,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            severity=severity,
            description=description,
            extra_data=extra_data
        )
        
        # Добавить в буфер
        self.performance_buffer.append(anomaly_event)
        
        # Отправить уведомление
        self._send_performance_notification(anomaly_event)
        
        # Записать в лог
        self._log_performance_anomaly(anomaly_event)
        
        # Отследить в системе мониторинга
        self.enhanced_monitoring.track_error(
            component=component,
            error_type=f"performance_{anomaly_type.value}",
            severity=severity.value,
            error_category='performance'
        )
        
        return anomaly_event
    
    def track_request_time(self, component: str, duration: float, is_error: bool = False):
        """
        Отследить время выполнения запроса.
        
        Args:
            component: Компонент системы
            duration: Продолжительность в секундах
            is_error: Признак ошибки
        """
        self.request_times[component].append((time.time(), duration, is_error))
        
        # Если это ошибка, увеличить счетчик ошибок
        if is_error:
            self.component_error_counts[component][ErrorType.PERFORMANCE.value] += 1
        
        # Увеличить общий счетчик запросов
        self.component_request_counts[component] += 1
    
    def _classify_exception(self, exception: Exception) -> Tuple[ErrorType, ErrorPriority]:
        """
        Классифицировать исключение по типу и приоритету.
        
        Args:
            exception: Исключение для классификации
            
        Returns:
            Tuple[ErrorType, ErrorPriority]: Тип ошибки и приоритет
        """
        exception_type = type(exception).__name__.lower()
        
        # Классификация по типу исключения
        if 'database' in exception_type or 'db' in exception_type:
            error_type = ErrorType.DATABASE
        elif 'connection' in exception_type or 'timeout' in exception_type or 'network' in exception_type:
            error_type = ErrorType.NETWORK
        elif 'auth' in exception_type or 'permission' in exception_type or 'unauthorized' in exception_type:
            error_type = ErrorType.AUTHENTICATION
        elif 'validation' in exception_type or 'value' in exception_type:
            error_type = ErrorType.VALIDATION
        elif 'external' in exception_type or 'api' in exception_type:
            error_type = ErrorType.EXTERNAL_SERVICE
        else:
            error_type = ErrorType.EXCEPTION
        
        # Определение приоритета по типу исключения
        high_priority_exceptions = [
            'databaseerror', 'connectionerror', 'timeouterror', 'permissionerror',
            'authenticationerror', 'systemerror', 'memoryerror', 'interruptederror'
        ]
        
        if exception_type in high_priority_exceptions:
            priority = ErrorPriority.HIGH
        elif 'error' in exception_type:
            priority = ErrorPriority.MEDIUM
        else:
            priority = ErrorPriority.LOW
        
        # Повысить приоритет для критических исключений
        critical_exceptions = [
            'systemexit', 'keyboardinterrupt', 'memoryerror', 'recursionerror'
        ]
        
        if exception_type in critical_exceptions:
            priority = ErrorPriority.CRITICAL
        
        return error_type, priority
    
    def _determine_anomaly_severity(self, current_value: float, threshold_value: float, anomaly_type: AnomalyType) -> ErrorPriority:
        """
        Определить уровень важности аномалии.
        
        Args:
            current_value: Текущее значение
            threshold_value: Пороговое значение
            anomaly_type: Тип аномалии
            
        Returns:
            ErrorPriority: Приоритет аномалии
        """
        ratio = current_value / threshold_value if threshold_value != 0 else float('inf')
        
        if ratio >= 3.0:  # значение в 3 раза превышает порог
            return ErrorPriority.CRITICAL
        elif ratio >= 2.0:  # значение в 2 раза превышает порог
            return ErrorPriority.HIGH
        elif ratio >= 1.5:  # значение в 1.5 раза превышает порог
            return ErrorPriority.MEDIUM
        else:
            return ErrorPriority.LOW
    
    async def _detect_performance_anomalies(self):
        """Обнаружить аномалии в производительности."""
        current_time = time.time()
        window_start = current_time - self.anomaly_detection_window
        
        # Проверить частоту ошибок
        for component, error_timers in self.component_error_timers.items():
            # Фильтровать таймеры в пределах окна
            recent_errors = [t for t in error_timers if t >= window_start]
            total_requests = self.component_request_counts[component]
            
            if total_requests > 0:
                error_rate = len(recent_errors) / total_requests
                
                if error_rate > self.high_error_rate_threshold:
                    self.track_performance_anomaly(
                        anomaly_type=AnomalyType.HIGH_ERROR_RATE,
                        component=component,
                        metric_name="error_rate",
                        current_value=error_rate,
                        threshold_value=self.high_error_rate_threshold,
                        description=f"High error rate detected: {error_rate:.2%} (threshold: {self.high_error_rate_threshold:.2%})",
                        extra_data={
                            "total_requests": total_requests,
                            "error_count": len(recent_errors)
                        }
                    )
        
        # Проверить высокую задержку
        for component, times in self.request_times.items():
            recent_times = [(t, d, e) for t, d, e in times if t >= window_start and not e]  # только успешные запросы
            if recent_times:
                avg_latency = sum(d for t, d, e in recent_times) / len(recent_times)
                
                if avg_latency > self.high_latency_threshold:
                    self.track_performance_anomaly(
                        anomaly_type=AnomalyType.HIGH_LATENCY,
                        component=component,
                        metric_name="avg_latency",
                        current_value=avg_latency,
                        threshold_value=self.high_latency_threshold,
                        description=f"High average latency detected: {avg_latency:.2f}s (threshold: {self.high_latency_threshold:.2f}s)",
                        extra_data={
                            "request_count": len(recent_times)
                        }
                    )
    
    def _send_notification(self, error_event: ErrorEvent):
        """Отправить уведомление об ошибке."""
        try:
            if self.notification_callback:
                self.notification_callback(error_event)
            
            # Также отправить в систему логирования
            self.logger.error(
                f"Error detected: {error_event.message}",
                extra={
                    'component': error_event.component,
                    'error_type': error_event.error_type.value,
                    'priority': error_event.priority.value,
                    'user_id': error_event.user_id,
                    'chat_id': error_event.chat_id,
                    'command': error_event.command,
                    'traceback': error_event.traceback_info
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")
    
    def _send_performance_notification(self, anomaly_event: PerformanceAnomaly):
        """Отправить уведомление об аномалии производительности."""
        try:
            # Отправить в систему логирования
            self.logger.warning(
                f"Performance anomaly detected: {anomaly_event.description}",
                extra={
                    'component': anomaly_event.component,
                    'anomaly_type': anomaly_event.anomaly_type.value,
                    'severity': anomaly_event.severity.value,
                    'metric_name': anomaly_event.metric_name,
                    'current_value': anomaly_event.current_value,
                    'threshold_value': anomaly_event.threshold_value
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to send performance notification: {e}")
    
    def _log_error_event(self, error_event: ErrorEvent):
        """Записать событие ошибки в лог."""
        self.enhanced_monitoring.log_structured(
            level=error_event.priority.value,
            message=error_event.message,
            component=error_event.component,
            error_type=error_event.error_type.value,
            priority=error_event.priority.value,
            user_id=error_event.user_id,
            chat_id=error_event.chat_id,
            command=error_event.command,
            traceback=error_event.traceback_info,
            extra_data=error_event.extra_data
        )
    
    def _log_performance_anomaly(self, anomaly_event: PerformanceAnomaly):
        """Записать событие аномалии в лог."""
        self.enhanced_monitoring.log_structured(
            level=anomaly_event.severity.value,
            message=anomaly_event.description,
            component=anomaly_event.component,
            anomaly_type=anomaly_event.anomaly_type.value,
            severity=anomaly_event.severity.value,
            metric_name=anomaly_event.metric_name,
            current_value=anomaly_event.current_value,
            threshold_value=anomaly_event.threshold_value,
            extra_data=anomaly_event.extra_data
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получить статистику по ошибкам."""
        current_time = time.time()
        window_start = current_time - self.anomaly_detection_window
        
        stats = {
            'total_errors': len(self.error_buffer),
            'total_anomalies': len(self.performance_buffer),
            'component_error_counts': dict(self.component_error_counts),
            'component_request_counts': dict(self.component_request_counts),
            'recent_errors': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'component': e.component,
                    'error_type': e.error_type.value,
                    'priority': e.priority.value,
                    'message': e.message
                }
                for e in list(self.error_buffer)[-10:]  # последние 10 ошибок
            ],
            'recent_anomalies': [
                {
                    'timestamp': a.timestamp.isoformat(),
                    'component': a.component,
                    'anomaly_type': a.anomaly_type.value,
                    'severity': a.severity.value,
                    'description': a.description
                }
                for a in list(self.performance_buffer)[-10:]  # последние 10 аномалий
            ]
        }
        
        return stats
    
    def reset_statistics(self):
        """Сбросить статистику ошибок."""
        self.error_buffer.clear()
        self.performance_buffer.clear()
        self.component_error_counts.clear()
        self.component_request_counts.clear()
        self.component_error_timers.clear()
        self.request_times.clear()


# Глобальный экземпляр детектора ошибок
realtime_error_detector = RealtimeErrorDetector()