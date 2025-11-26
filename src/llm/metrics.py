"""
LLM Metrics Collection
Сбор и экспорт метрик для мониторинга LLM системы
"""

import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = Info = None

logger = logging.getLogger(__name__)


@dataclass
class MetricsData:
    """Данные метрик"""
    
    # Счетчики запросов
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Использование провайдеров
    provider_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    provider_errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Время отклика
    response_times: list = field(default_factory=list)
    
    # Кэш
    cache_hits: int = 0
    cache_misses: int = 0
    
    # Rate limiting
    rate_limit_hits: int = 0
    
    # Токены
    total_tokens_used: int = 0
    
    # Временные метки
    start_time: datetime = field(default_factory=datetime.now)
    last_request_time: Optional[datetime] = None
    
    def get_success_rate(self) -> float:
        """Процент успешных запросов"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_cache_hit_rate(self) -> float:
        """Процент попаданий в кэш"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100
    
    def get_average_response_time(self) -> float:
        """Среднее время отклика в секундах"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_uptime(self) -> timedelta:
        """Время работы системы"""
        return datetime.now() - self.start_time


class LLMMetrics:
    """
    Сбор метрик для LLM системы
    
    Поддерживает:
    - Prometheus метрики (если установлен prometheus-client)
    - Внутренние метрики для статистики
    """
    
    def __init__(self, enable_prometheus: bool = True):
        """
        Инициализация системы метрик.
        
        Args:
            enable_prometheus: Включить Prometheus метрики
        """
        self.data = MetricsData()
        self.prometheus_enabled = enable_prometheus and PROMETHEUS_AVAILABLE
        
        # Инициализация Prometheus метрик
        if self.prometheus_enabled:
            self._init_prometheus_metrics()
            logger.info("✅ Prometheus metrics enabled")
        else:
            if enable_prometheus and not PROMETHEUS_AVAILABLE:
                logger.warning(
                    "⚠️ Prometheus client not installed. "
                    "Install with: pip install prometheus-client"
                )
            logger.info("📊 Using internal metrics only")
    
    def _init_prometheus_metrics(self):
        """Инициализация Prometheus метрик"""
        # Счетчики запросов
        self.prom_requests_total = Counter(
            'llm_requests_total',
            'Total number of LLM requests',
            ['provider', 'status']
        )
        
        # Время отклика
        self.prom_request_duration = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['provider']
        )
        
        # Кэш
        self.prom_cache_hits = Counter(
            'llm_cache_hits_total',
            'Total number of cache hits'
        )
        
        self.prom_cache_misses = Counter(
            'llm_cache_misses_total',
            'Total number of cache misses'
        )
        
        # Rate limiting
        self.prom_rate_limit_hits = Counter(
            'llm_rate_limit_hits_total',
            'Total number of rate limit hits',
            ['provider']
        )
        
        # Токены
        self.prom_tokens_used = Counter(
            'llm_tokens_used_total',
            'Total number of tokens used',
            ['provider']
        )
        
        # Активные провайдеры
        self.prom_active_providers = Gauge(
            'llm_active_providers',
            'Number of active LLM providers'
        )
        
        # Информация о системе
        self.prom_info = Info(
            'llm_system',
            'LLM system information'
        )
    
    def record_request(
        self,
        provider: str,
        success: bool,
        duration: float,
        tokens: int = 0,
        error: Optional[str] = None
    ):
        """
        Запись метрик запроса.
        
        Args:
            provider: Имя провайдера
            success: Успешность запроса
            duration: Длительность в секундах
            tokens: Количество использованных токенов
            error: Сообщение об ошибке (если есть)
        """
        # Обновление внутренних метрик
        self.data.total_requests += 1
        self.data.last_request_time = datetime.now()
        
        if success:
            self.data.successful_requests += 1
        else:
            self.data.failed_requests += 1
            self.data.provider_errors[provider] += 1
        
        self.data.provider_usage[provider] += 1
        self.data.response_times.append(duration)
        self.data.total_tokens_used += tokens
        
        # Ограничение размера списка времен отклика
        if len(self.data.response_times) > 1000:
            self.data.response_times = self.data.response_times[-1000:]
        
        # Prometheus метрики
        if self.prometheus_enabled:
            status = 'success' if success else 'error'
            self.prom_requests_total.labels(
                provider=provider,
                status=status
            ).inc()
            
            self.prom_request_duration.labels(
                provider=provider
            ).observe(duration)
            
            if tokens > 0:
                self.prom_tokens_used.labels(
                    provider=provider
                ).inc(tokens)
        
        # Логирование
        if success:
            logger.debug(
                f"✅ Request to {provider}: {duration:.2f}s, {tokens} tokens"
            )
        else:
            logger.warning(
                f"❌ Request to {provider} failed: {error}"
            )
    
    def record_cache_hit(self):
        """Запись попадания в кэш"""
        self.data.cache_hits += 1
        
        if self.prometheus_enabled:
            self.prom_cache_hits.inc()
    
    def record_cache_miss(self):
        """Запись промаха кэша"""
        self.data.cache_misses += 1
        
        if self.prometheus_enabled:
            self.prom_cache_misses.inc()
    
    def record_rate_limit_hit(self, provider: str):
        """Запись срабатывания rate limit"""
        self.data.rate_limit_hits += 1
        
        if self.prometheus_enabled:
            self.prom_rate_limit_hits.labels(
                provider=provider
            ).inc()
        
        logger.warning(f"⚠️ Rate limit hit for provider: {provider}")
    
    def update_active_providers(self, count: int):
        """Обновление количества активных провайдеров"""
        if self.prometheus_enabled:
            self.prom_active_providers.set(count)
    
    def set_system_info(self, info: Dict[str, str]):
        """Установка информации о системе"""
        if self.prometheus_enabled:
            self.prom_info.info(info)
    
    def get_statistics(self) -> dict:
        """
        Получение статистики.
        
        Returns:
            Словарь со статистикой
        """
        return {
            'total_requests': self.data.total_requests,
            'successful_requests': self.data.successful_requests,
            'failed_requests': self.data.failed_requests,
            'success_rate': self.data.get_success_rate(),
            
            'provider_usage': dict(self.data.provider_usage),
            'provider_errors': dict(self.data.provider_errors),
            
            'average_response_time': self.data.get_average_response_time(),
            'total_tokens_used': self.data.total_tokens_used,
            
            'cache_hits': self.data.cache_hits,
            'cache_misses': self.data.cache_misses,
            'cache_hit_rate': self.data.get_cache_hit_rate(),
            
            'rate_limit_hits': self.data.rate_limit_hits,
            
            'uptime_seconds': self.data.get_uptime().total_seconds(),
            'last_request': self.data.last_request_time.isoformat() if self.data.last_request_time else None
        }
    
    def get_dashboard_data(self) -> dict:
        """
        Получение данных для dashboard.
        
        Returns:
            Словарь с форматированными данными
        """
        stats = self.get_statistics()
        
        # Форматирование для отображения
        return {
            'overview': {
                'total_requests': stats['total_requests'],
                'success_rate': f"{stats['success_rate']:.1f}%",
                'avg_response_time': f"{stats['average_response_time']:.2f}s",
                'uptime': str(self.data.get_uptime()).split('.')[0]  # Без микросекунд
            },
            'providers': {
                name: {
                    'requests': count,
                    'errors': stats['provider_errors'].get(name, 0),
                    'error_rate': f"{(stats['provider_errors'].get(name, 0) / count * 100):.1f}%" if count > 0 else "0%"
                }
                for name, count in stats['provider_usage'].items()
            },
            'cache': {
                'hits': stats['cache_hits'],
                'misses': stats['cache_misses'],
                'hit_rate': f"{stats['cache_hit_rate']:.1f}%"
            },
            'tokens': {
                'total': stats['total_tokens_used'],
                'per_request': f"{stats['total_tokens_used'] / stats['total_requests']:.0f}" if stats['total_requests'] > 0 else "0"
            }
        }
    
    def reset_statistics(self):
        """Сброс статистики"""
        self.data = MetricsData()
        logger.info("📊 Metrics reset")
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return (
            f"LLMMetrics("
            f"requests={stats['total_requests']}, "
            f"success_rate={stats['success_rate']:.1f}%, "
            f"cache_hit_rate={stats['cache_hit_rate']:.1f}%)"
        )


# Глобальный экземпляр метрик
_metrics: Optional[LLMMetrics] = None


def get_metrics() -> LLMMetrics:
    """
    Получение глобального экземпляра метрик.
    
    Returns:
        LLMMetrics
    """
    global _metrics
    
    if _metrics is None:
        _metrics = LLMMetrics()
    
    return _metrics


def reset_metrics():
    """Сброс глобальных метрик"""
    global _metrics
    _metrics = None
