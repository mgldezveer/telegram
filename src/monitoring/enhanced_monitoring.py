"""Улучшенная система мониторинга и логирования."""

import logging
import time
import asyncio
from typing import Optional, Callable, Any, Dict, List
from functools import wraps
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from aiohttp import web
from dataclasses import dataclass
import json
import traceback
from enum import Enum

from src.cache import cache

logger = logging.getLogger(__name__)


class MonitoringLogLevel(Enum):
    """Уровни логирования для мониторинга."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Запись лога."""
    timestamp: datetime
    level: str
    message: str
    component: str
    extra: dict


# Улучшенные метрики Prometheus
# Метрики для генерации контента
posts_generated = Counter(
    'posts_generated_total',
    'Total posts generated',
    ['channel_id', 'status', 'style_tone', 'style_length', 'content_type']
)
posts_generation_duration = Histogram(
    'posts_generation_duration_seconds',
    'Time spent generating posts',
    ['channel_id', 'content_type'],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
)

# Метрики для публикации
posts_published = Counter(
    'posts_published_total',
    'Total posts published',
    ['channel_id', 'success', 'content_type']
)
posts_publishing_duration = Histogram(
    'posts_publishing_duration_seconds',
    'Time spent publishing posts',
    ['channel_id', 'content_type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# Метрики для ошибок
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['component', 'error_type', 'severity', 'error_category']
)

# Метрики для производительности
active_tasks = Gauge('active_tasks', 'Number of active tasks')
memory_usage = Gauge('memory_usage_bytes', 'Current memory usage')
cpu_usage = Gauge('cpu_usage_percent', 'Current CPU usage percent')
process_uptime = Gauge('process_uptime_seconds', 'Process uptime in seconds')

# Метрики для кэша
cache_hits = Counter('cache_hits_total', 'Total cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Total cache misses', ['cache_type'])
cache_size = Gauge('cache_size', 'Current cache size', ['cache_type'])
cache_operations = Counter('cache_operations_total', 'Total cache operations', ['operation', 'cache_type'])
cache_evictions = Counter('cache_evictions_total', 'Total cache evictions', ['cache_type'])

# Метрики для базы данных
db_queries_total = Counter('db_queries_total', 'Total database queries', ['query_type', 'db_type'])
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Time spent on database queries',
    ['query_type', 'db_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
)

# Метрики для LLM
llm_requests_total = Counter('llm_requests_total', 'Total LLM requests', ['provider', 'model'])
llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'Time spent on LLM requests',
    ['provider', 'model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)
llm_tokens_total = Counter('llm_tokens_total', 'Total LLM tokens processed', ['direction'])  # direction: input/output
llm_errors_total = Counter('llm_errors_total', 'Total LLM errors', ['provider', 'error_type'])

# Метрики для планировщика
scheduled_posts = Counter('scheduled_posts_total', 'Total scheduled posts', ['channel_id'])
executed_schedules = Counter('executed_schedules_total', 'Total executed schedules', ['schedule_type'])
failed_schedules = Counter('failed_schedules_total', 'Total failed schedules', ['schedule_type'])

# Метрики для каналов
active_channels = Gauge('active_channels', 'Number of active channels')
channel_subscribers = Gauge('channel_subscribers', 'Number of subscribers per channel', ['channel_id'])
channel_errors = Counter('channel_errors_total', 'Total channel errors', ['channel_id', 'error_type'])

# Метрики для бота
bot_commands_total = Counter('bot_commands_total', 'Total bot commands processed', ['command', 'user_id'])
bot_errors_total = Counter('bot_errors_total', 'Total bot errors', ['command', 'error_type'])

# Системная информация
system_info = Info('system', 'System information')
system_info.info({'version': '1.0.0', 'service': 'ai-content-bot'})


class EnhancedMonitoring:
    """Улучшенная система мониторинга и логирования."""
    
    def __init__(self, log_buffer_size: int = 1000, metrics_interval: int = 30):
        self.log_buffer: List[LogEntry] = []
        self.max_log_buffer_size = log_buffer_size
        self.metrics_collection_interval = metrics_interval  # seconds
        self._running = False
        self._metrics_task: Optional[asyncio.Task] = None
        self.start_time = time.time()
        
        # Статистика для отчетов
        self.stats = {
            'posts_generated': 0,
            'posts_published': 0,
            'errors_count': 0,
            'active_channels_count': 0,
            'llm_requests': 0,
            'db_queries': 0
        }
    
    def track_llm_request(self, provider: str, model: str, duration: float, input_tokens: int = 0, output_tokens: int = 0, success: bool = True):
        """Отследить запрос к LLM.
        
        Args:
            provider: Провайдер LLM
            model: Модель LLM
            duration: Продолжительность запроса в секундах
            input_tokens: Количество входных токенов
            output_tokens: Количество выходных токенов
            success: Успешность запроса
        """
        llm_requests_total.labels(provider=provider, model=model).inc()
        llm_request_duration.labels(provider=provider, model=model).observe(duration)
        
        if input_tokens > 0:
            llm_tokens_total.labels(direction='input').inc(input_tokens)
        if output_tokens > 0:
            llm_tokens_total.labels(direction='output').inc(output_tokens)
        
        self.stats['llm_requests'] += 1
        
        if not success:
            llm_errors_total.labels(provider=provider, error_type='request_failed').inc()
    
    def track_db_query(self, query_type: str, db_type: str, duration: float, success: bool = True):
        """Отследить запрос к базе данных.
        
        Args:
            query_type: Тип запроса (select, insert, update, delete)
            db_type: Тип базы данных
            duration: Продолжительность запроса в секундах
            success: Успешность запроса
        """
        db_queries_total.labels(query_type=query_type, db_type=db_type).inc()
        db_query_duration.labels(query_type=query_type, db_type=db_type).observe(duration)
        
        self.stats['db_queries'] += 1
        
        if not success:
            self.track_error('database', f'db_{query_type}_failed', 'error')
    
    def track_cache_operation(self, operation: str, cache_type: str, hit: Optional[bool] = None, evicted: bool = False):
        """Отследить операцию с кэшем.
        
        Args:
            operation: Тип операции (get, set, delete)
            cache_type: Тип кэша (redis, memory)
            hit: Результат операции для get (hit/miss)
            evicted: Были ли элементы вытеснены из кэша
        """
        cache_operations.labels(operation=operation, cache_type=cache_type).inc()
        
        if operation == 'get' and hit is not None:
            if hit:
                cache_hits.labels(cache_type=cache_type).inc()
            else:
                cache_misses.labels(cache_type=cache_type).inc()
        
        if evicted:
            cache_evictions.labels(cache_type=cache_type).inc()
    
    def track_post_generation(self, channel_id: str, style_tone: str, style_length: str, duration: float, content_type: str = 'text'):
        """Отследить генерацию поста.
        
        Args:
            channel_id: ID канала
            style_tone: Тон стиля
            style_length: Длина стиля
            duration: Продолжительность генерации в секундах
            content_type: Тип контента (text, image, video)
        """
        posts_generated.labels(
            channel_id=channel_id,
            status='success',
            style_tone=style_tone,
            style_length=style_length,
            content_type=content_type
        ).inc()
        
        posts_generation_duration.labels(channel_id=channel_id, content_type=content_type).observe(duration)
        self.stats['posts_generated'] += 1
    
    def track_post_publication(self, channel_id: str, success: bool, duration: float, content_type: str = 'text'):
        """Отследить публикацию поста.
        
        Args:
            channel_id: ID канала
            success: Успешность публикации
            duration: Продолжительность публикации в секундах
            content_type: Тип контента (text, image, video)
        """
        posts_published.labels(channel_id=channel_id, success=str(success), content_type=content_type).inc()
        posts_publishing_duration.labels(channel_id=channel_id, content_type=content_type).observe(duration)
        
        if success:
            self.stats['posts_published'] += 1
        else:
            self.track_error('publication', 'publish_failed', 'error')
    
    def track_error(self, component: str, error_type: str, severity: str = 'error', error_category: str = 'general'):
        """Отследить ошибку.
        
        Args:
            component: Компонент системы
            error_type: Тип ошибки
            severity: Уровень важности
            error_category: Категория ошибки
        """
        errors_total.labels(
            component=component, 
            error_type=error_type, 
            severity=severity,
            error_category=error_category
        ).inc()
        self.stats['errors_count'] += 1
    
    def track_schedule_execution(self, schedule_type: str, success: bool = True):
        """Отследить выполнение расписания.
        
        Args:
            schedule_type: Тип расписания
            success: Успешность выполнения
        """
        if success:
            executed_schedules.labels(schedule_type=schedule_type).inc()
        else:
            failed_schedules.labels(schedule_type=schedule_type).inc()
    
    def track_channel_error(self, channel_id: str, error_type: str):
        """Отследить ошибку канала.
        
        Args:
            channel_id: ID канала
            error_type: Тип ошибки
        """
        channel_errors.labels(channel_id=channel_id, error_type=error_type).inc()
        self.track_error('channel', error_type, 'error', 'channel')
    
    def track_bot_command(self, command: str, user_id: str):
        """Отследить выполнение команды бота.
        
        Args:
            command: Команда
            user_id: ID пользователя
        """
        bot_commands_total.labels(command=command, user_id=user_id).inc()
    
    def track_bot_error(self, command: str, error_type: str):
        """Отследить ошибку бота.
        
        Args:
            command: Команда
            error_type: Тип ошибки
        """
        bot_errors_total.labels(command=command, error_type=error_type).inc()
        self.track_error('bot', error_type, 'error', 'bot')
    
    def update_active_channels(self, count: int):
        """Обновить количество активных каналов.
        
        Args:
            count: Количество активных каналов
        """
        active_channels.set(count)
        self.stats['active_channels_count'] = count
    
    def update_channel_subscribers(self, channel_id: str, count: int):
        """Обновить количество подписчиков канала.
        
        Args:
            channel_id: ID канала
            count: Количество подписчиков
        """
        channel_subscribers.labels(channel_id=channel_id).set(count)
    
    def update_cache_size(self, cache_type: str, size: int):
        """Обновить размер кэша.
        
        Args:
            cache_type: Тип кэша
            size: Размер кэша
        """
        cache_size.labels(cache_type=cache_type).set(size)
    
    async def collect_system_metrics(self):
        """Собрать системные метрики (память, CPU и т.д.)."""
        try:
            import psutil
            
            # Сбор метрик производительности
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            memory_usage.set(memory_info.rss)
            cpu_usage.set(cpu_percent)
            active_tasks.set(len(asyncio.all_tasks()))
            process_uptime.set(time.time() - self.start_time)
            
        except ImportError:
            logger.warning("psutil not available, skipping system metrics collection")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def collect_cache_metrics(self):
        """Собрать метрики кэша."""
        try:
            # Получить статистику из Redis
            if hasattr(cache, 'is_redis_available') and cache.is_redis_available():
                redis_info = await cache._redis_cache._client.info()
                self.update_cache_size('redis', redis_info.get('used_memory', 0))
            
            # Получить статистику из памяти
            if hasattr(cache, '_memory_cache'):
                mem_stats = cache._memory_cache.get_stats()
                self.update_cache_size('memory', mem_stats.get('current_size', 0))
                
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
    
    async def start_metrics_collection(self):
        """Запустить сбор метрик."""
        if self._running:
            return
        
        self._running = True
        self._metrics_task = asyncio.create_task(self._metrics_collection_loop())
        logger.info("Enhanced metrics collection started")
    
    async def stop_metrics_collection(self):
        """Остановить сбор метрик."""
        self._running = False
        if self._metrics_task:
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
        logger.info("Enhanced metrics collection stopped")
    
    async def _metrics_collection_loop(self):
        """Цикл сбора метрик."""
        while self._running:
            try:
                await self.collect_system_metrics()
                await self.collect_cache_metrics()
                await asyncio.sleep(self.metrics_collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.metrics_collection_interval)
    
    def get_stats_report(self) -> dict:
        """Получить отчет о статистике.
        
        Returns:
            Словарь со статистикой
        """
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'stats': self.stats.copy(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def log_structured(self, level: str, message: str, component: str, **kwargs):
        """Логировать структурированное сообщение.
        
        Args:
            level: Уровень логирования
            message: Сообщение
            component: Компонент системы
            **kwargs: Дополнительные данные
        """
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            component=component,
            extra=kwargs
        )
        
        self.log_buffer.append(entry)
        
        # Ограничить размер буфера
        if len(self.log_buffer) > self.max_log_buffer_size:
            self.log_buffer = self.log_buffer[-self.max_log_buffer_size:]
        
        # Записать в лог
        logger.log(getattr(logging, level.upper(), logging.INFO), message, extra=kwargs)


def track_content_generation_time(func: Callable) -> Callable:
    """Декоратор для отслеживания времени генерации контента."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        monitoring = EnhancedMonitoring()  # Получить экземпляр мониторинга
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Извлечь параметры для метрик
            channel_id = kwargs.get('channel_id', 'unknown')
            style = kwargs.get('style')
            content_type = kwargs.get('content_type', 'text')
            if style and hasattr(style, 'tone') and hasattr(style, 'length'):
                monitoring.track_post_generation(
                    str(channel_id),
                    style.tone,
                    style.length,
                    duration,
                    content_type
                )
            else:
                monitoring.track_post_generation(str(channel_id), 'unknown', 'unknown', duration, content_type)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            monitoring.track_post_generation(
                str(kwargs.get('channel_id', 'unknown')),
                'unknown',
                'unknown',
                duration,
                kwargs.get('content_type', 'text')
            )
            monitoring.track_error('content_generation', type(e).__name__, 'error')
            raise
    
    return wrapper


def track_publication_time(func: Callable) -> Callable:
    """Декоратор для отслеживания времени публикации."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        monitoring = EnhancedMonitoring()  # Получить экземпляр мониторинга
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Извлечь параметры для метрик
            channel_id = kwargs.get('channel_id', 'unknown')
            content_type = kwargs.get('content_type', 'text')
            
            # Проверить успешность публикации
            success = True
            if hasattr(result, 'success'):
                success = result.success
            elif hasattr(result, 'message_id'):
                success = result.message_id is not None
            
            monitoring.track_post_publication(str(channel_id), success, duration, content_type)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            monitoring.track_post_publication(
                str(kwargs.get('channel_id', 'unknown')),
                False,
                duration,
                kwargs.get('content_type', 'text')
            )
            monitoring.track_error('publication', type(e).__name__, 'error')
            raise
    
    return wrapper


# Глобальный экземпляр улучшенного мониторинга
enhanced_monitoring = EnhancedMonitoring()


async def enhanced_metrics_handler(request):
    """Улучшенная точка доступа к метрикам Prometheus."""
    # Обновить системную информацию
    import platform
    system_info.info({
        'version': '1.0.0',
        'service': 'ai-content-bot',
        'platform': platform.platform(),
        'python_version': platform.python_version()
    })
    
    metrics_data = generate_latest()
    return web.Response(
        body=metrics_data,
        content_type=CONTENT_TYPE_LATEST
    )


async def enhanced_health_handler(request):
    """Улучшенная точка проверки работоспособности."""
    from src.database.enhanced_db import enhanced_db
    
    # Проверить основные компоненты
    checks = {
        'database': False,
        'cache': False,
        'llm': False
    }
    
    try:
        # Проверить базу данных
        db_health = await enhanced_db.health_check()
        checks['database'] = db_health.get('healthy', False)
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    try:
        # Проверить кэш
        cache_health = await cache.health_check()
        checks['cache'] = cache_health.get('healthy', False)
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
    
    try:
        # Проверить LLM (если доступно)
        from src.llm import get_llm_manager
        llm_manager = get_llm_manager()
        if llm_manager:
            checks['llm'] = await llm_manager.health_check()
        else:
            checks['llm'] = True  # Не считаем ошибкой если LLM не настроен
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        checks['llm'] = True # Не считаем критической ошибкой
    
    overall_health = all(checks.values())
    
    health_status = {
        'status': 'healthy' if overall_health else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': time.time() - enhanced_monitoring.start_time
    }
    
    status_code = 200 if overall_health else 503
    return web.json_response(health_status, status=status_code)


async def stats_handler(request):
    """Точка доступа к статистике."""
    stats = enhanced_monitoring.get_stats_report()
    return web.json_response(stats)


async def start_enhanced_monitoring_server(port: int = 9091) -> web.AppRunner:
    """Запустить улучшенный сервер мониторинга.
    
    Args:
        port: Порт для сервера мониторинга (по умолчанию 9091)
        
    Returns:
        AppRunner для корректного завершения
    """
    app = web.Application()
    
    # Добавить маршруты
    app.router.add_get('/metrics', enhanced_metrics_handler)
    app.router.add_get('/health', enhanced_health_handler)
    app.router.add_get('/stats', stats_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    try:
        site = web.TCPSite(runner, '0.0.0', port)
        await site.start()
        logger.info(f"Enhanced monitoring server started on port {port}")
        
        # Запустить сбор метрик
        await enhanced_monitoring.start_metrics_collection()
        
        return runner
    except OSError as e:
        logger.error(f"Failed to start enhanced monitoring server on port {port}: {e}")
        await runner.cleanup()
        raise


async def stop_enhanced_monitoring_server(runner: web.AppRunner) -> None:
    """Остановить улучшенный сервер мониторинга.
    
    Args:
        runner: AppRunner для остановки
    """
    if runner:
        logger.info("Stopping enhanced monitoring server...")
        
        # Остановить сбор метрик
        await enhanced_monitoring.stop_metrics_collection()
        
        await runner.cleanup()
        logger.info("Enhanced monitoring server stopped")