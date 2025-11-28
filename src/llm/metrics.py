"""
LLM Metrics - Prometheus metrics and monitoring for LLM operations
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = Info = None

logger = logging.getLogger(__name__)


class LLMMetrics:
    """
    LLM Metrics collector for monitoring and observability.
    
    Tracks:
    - Request counts per provider
    - Response latencies
    - Error rates
    - Cache hit rates
    - Rate limit events
    """
    
    def __init__(self, enable_prometheus: bool = True):
        """
        Initialize metrics collector.
        
        Args:
            enable_prometheus: Whether to use Prometheus metrics
        """
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        
        if self.enable_prometheus:
            self._init_prometheus_metrics()
            logger.info("✅ LLM Metrics initialized with Prometheus")
        else:
            logger.info("✅ LLM Metrics initialized (Prometheus disabled)")
        
        # In-memory metrics fallback
        self.memory_metrics = {
            'requests_total': {},
            'requests_success': {},
            'requests_failed': {},
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_hits': {},
            'latencies': {},
            'errors': {}
        }
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        # Request counters
        self.requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['provider', 'status']
        )
        
        # Latency histogram
        self.request_duration = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['provider'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'llm_cache_hits_total',
            'Total cache hits'
        )
        
        self.cache_misses = Counter(
            'llm_cache_misses_total',
            'Total cache misses'
        )
        
        # Rate limit events
        self.rate_limit_hits = Counter(
            'llm_rate_limit_hits_total',
            'Total rate limit hits',
            ['provider']
        )
        
        # Active requests gauge
        self.active_requests = Gauge(
            'llm_active_requests',
            'Number of active LLM requests',
            ['provider']
        )
        
        # Provider info
        self.provider_info = Info(
            'llm_provider',
            'LLM provider information'
        )
    
    def record_request(
        self,
        provider: str,
        success: bool,
        duration: float,
        error: Optional[str] = None
    ):
        """
        Record a request.
        
        Args:
            provider: Provider name
            success: Whether request succeeded
            duration: Request duration in seconds
            error: Optional error message
        """
        status = 'success' if success else 'failed'
        
        # Prometheus metrics
        if self.enable_prometheus:
            self.requests_total.labels(provider=provider, status=status).inc()
            self.request_duration.labels(provider=provider).observe(duration)
        
        # Memory metrics
        if provider not in self.memory_metrics['requests_total']:
            self.memory_metrics['requests_total'][provider] = 0
            self.memory_metrics['requests_success'][provider] = 0
            self.memory_metrics['requests_failed'][provider] = 0
            self.memory_metrics['latencies'][provider] = []
        
        self.memory_metrics['requests_total'][provider] += 1
        
        if success:
            self.memory_metrics['requests_success'][provider] += 1
        else:
            self.memory_metrics['requests_failed'][provider] += 1
            
            if error:
                if provider not in self.memory_metrics['errors']:
                    self.memory_metrics['errors'][provider] = []
                self.memory_metrics['errors'][provider].append({
                    'error': error,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        self.memory_metrics['latencies'][provider].append(duration)
        
        # Keep only last 1000 latencies
        if len(self.memory_metrics['latencies'][provider]) > 1000:
            self.memory_metrics['latencies'][provider] = \
                self.memory_metrics['latencies'][provider][-1000:]
    
    def record_cache_hit(self):
        """Record a cache hit"""
        if self.enable_prometheus:
            self.cache_hits.inc()
        
        self.memory_metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        if self.enable_prometheus:
            self.cache_misses.inc()
        
        self.memory_metrics['cache_misses'] += 1
    
    def record_rate_limit_hit(self, provider: str):
        """Record a rate limit hit"""
        if self.enable_prometheus:
            self.rate_limit_hits.labels(provider=provider).inc()
        
        if provider not in self.memory_metrics['rate_limit_hits']:
            self.memory_metrics['rate_limit_hits'][provider] = 0
        
        self.memory_metrics['rate_limit_hits'][provider] += 1
    
    def set_active_requests(self, provider: str, count: int):
        """Set number of active requests for provider"""
        if self.enable_prometheus:
            self.active_requests.labels(provider=provider).set(count)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'providers': {},
            'cache': {},
            'rate_limits': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Provider statistics
        for provider in self.memory_metrics['requests_total'].keys():
            total = self.memory_metrics['requests_total'][provider]
            success = self.memory_metrics['requests_success'][provider]
            failed = self.memory_metrics['requests_failed'][provider]
            
            success_rate = (success / total * 100) if total > 0 else 0
            
            latencies = self.memory_metrics['latencies'][provider]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            stats['providers'][provider] = {
                'total_requests': total,
                'successful': success,
                'failed': failed,
                'success_rate': round(success_rate, 2),
                'avg_latency_seconds': round(avg_latency, 3),
                'rate_limit_hits': self.memory_metrics['rate_limit_hits'].get(provider, 0)
            }
        
        # Cache statistics
        cache_total = self.memory_metrics['cache_hits'] + self.memory_metrics['cache_misses']
        cache_hit_rate = (self.memory_metrics['cache_hits'] / cache_total * 100) if cache_total > 0 else 0
        
        stats['cache'] = {
            'hits': self.memory_metrics['cache_hits'],
            'misses': self.memory_metrics['cache_misses'],
            'total': cache_total,
            'hit_rate': round(cache_hit_rate, 2)
        }
        
        # Rate limit statistics
        stats['rate_limits'] = self.memory_metrics['rate_limit_hits'].copy()
        
        return stats
    
    def get_dashboard_data(self) -> str:
        """
        Get formatted dashboard data for display.
        
        Returns:
            Formatted string with metrics
        """
        stats = self.get_statistics()
        
        lines = ["📊 LLM Metrics Dashboard"]
        lines.append("=" * 50)
        lines.append("")
        
        # Provider metrics
        lines.append("Providers:")
        for provider, metrics in stats['providers'].items():
            lines.append(f"  {provider.capitalize()}:")
            lines.append(f"    Total Requests: {metrics['total_requests']}")
            lines.append(f"    Success Rate: {metrics['success_rate']}%")
            lines.append(f"    Avg Latency: {metrics['avg_latency_seconds']}s")
            lines.append(f"    Rate Limit Hits: {metrics['rate_limit_hits']}")
            lines.append("")
        
        # Cache metrics
        lines.append("Cache:")
        lines.append(f"  Hit Rate: {stats['cache']['hit_rate']}%")
        lines.append(f"  Hits: {stats['cache']['hits']}")
        lines.append(f"  Misses: {stats['cache']['misses']}")
        lines.append("")
        
        # Timestamp
        lines.append(f"Last Updated: {stats['timestamp']}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        backend = "Prometheus" if self.enable_prometheus else "Memory"
        return f"LLMMetrics(backend={backend})"


# Global metrics instance
_metrics: Optional[LLMMetrics] = None


def get_metrics() -> LLMMetrics:
    """
    Get global metrics instance.
    
    Returns:
        LLMMetrics instance
    """
    global _metrics
    if _metrics is None:
        _metrics = LLMMetrics(enable_prometheus=PROMETHEUS_AVAILABLE)
    return _metrics


# Context manager for timing requests
class RequestTimer:
    """Context manager for timing LLM requests"""
    
    def __init__(self, provider: str, metrics: Optional[LLMMetrics] = None):
        self.provider = provider
        self.metrics = metrics or get_metrics()
        self.start_time = None
        self.success = False
        self.error = None
    
    def __enter__(self):
        self.start_time = time.time()
        if self.metrics.enable_prometheus:
            self.metrics.set_active_requests(self.provider, 1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.success = True
        else:
            self.error = str(exc_val)
        
        self.metrics.record_request(
            provider=self.provider,
            success=self.success,
            duration=duration,
            error=self.error
        )
        
        if self.metrics.enable_prometheus:
            self.metrics.set_active_requests(self.provider, 0)
        
        return False  # Don't suppress exceptions
