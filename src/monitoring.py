"""Monitoring and observability.

This module provides Prometheus metrics collection, health checks,
and monitoring endpoints for the AI Content Bot.
"""

import logging
import time
from typing import Optional, Callable, Any
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from aiohttp import web

logger = logging.getLogger(__name__)

# Prometheus metrics
posts_generated = Counter(
    'posts_generated_total',
    'Total posts generated',
    ['channel_id', 'status']
)
posts_published = Counter(
    'posts_published_total',
    'Total posts published',
    ['channel_id']
)
posts_failed = Counter(
    'posts_failed_total',
    'Total posts failed',
    ['channel_id', 'error_type']
)

generation_duration = Histogram(
    'generation_duration_seconds',
    'Time spent generating content',
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)
publishing_duration = Histogram(
    'publishing_duration_seconds',
    'Time spent publishing posts',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

active_channels = Gauge('active_channels', 'Number of active channels')
queue_size = Gauge('queue_size', 'Size of content queue', ['channel_id'])
error_count = Counter('errors_total', 'Total errors', ['category', 'severity'])

# Cache metrics
cache_hits = Counter('cache_hits_total', 'Total cache hits', ['backend'])
cache_misses = Counter('cache_misses_total', 'Total cache misses', ['backend'])
cache_size = Gauge('cache_size', 'Current cache size', ['backend'])
cache_memory_usage = Gauge('cache_memory_usage_bytes', 'Cache memory usage in bytes', ['backend'])


def track_generation_time(func: Callable) -> Callable:
    """Decorator to track content generation time.
    
    Args:
        func: Async function to wrap with timing metrics
        
    Returns:
        Wrapped function with timing instrumentation
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        channel_id = kwargs.get('channel_id', 'unknown')
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            generation_duration.observe(duration)
            
            # Track with labels if result has status
            status = getattr(result, 'status', 'success')
            posts_generated.labels(channel_id=str(channel_id), status=status).inc()
            
            return result
        except Exception as e:
            error_type = type(e).__name__
            posts_failed.labels(channel_id=str(channel_id), error_type=error_type).inc()
            logger.error(
                f"Content generation failed in {func.__name__}: {e}",
                exc_info=True,
                extra={'channel_id': channel_id, 'error_type': error_type}
            )
            raise
    return wrapper


def track_publishing_time(func: Callable) -> Callable:
    """Decorator to track publishing time.
    
    Args:
        func: Async function to wrap with timing metrics
        
    Returns:
        Wrapped function with timing instrumentation
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        channel_id = kwargs.get('channel_id', 'unknown')
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            publishing_duration.observe(duration)
            
            if hasattr(result, 'success') and result.success:
                posts_published.labels(channel_id=str(channel_id)).inc()
            else:
                error_type = getattr(result, 'error', 'unknown_error')
                posts_failed.labels(channel_id=str(channel_id), error_type=error_type).inc()
            
            return result
        except Exception as e:
            error_type = type(e).__name__
            posts_failed.labels(channel_id=str(channel_id), error_type=error_type).inc()
            logger.error(
                f"Publishing failed in {func.__name__}: {e}",
                exc_info=True,
                extra={'channel_id': channel_id, 'error_type': error_type}
            )
            raise
    return wrapper


class HealthCheck:
    """Health check service with detailed status tracking.
    
    Attributes:
        start_time: Timestamp when service started
        is_healthy: Overall health status flag
        component_health: Dict tracking health of individual components
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.is_healthy = True
        self.component_health: dict[str, bool] = {}
        self.last_check_time: Optional[float] = None
    
    async def check(self) -> dict:
        """Perform comprehensive health check.
        
        Returns:
            Dictionary containing health status, uptime, and component details
        """
        uptime = time.time() - self.start_time
        self.last_check_time = time.time()
        
        health_status = {
            'status': 'healthy' if self.is_healthy else 'unhealthy',
            'uptime_seconds': uptime,
            'timestamp': time.time(),
            'components': self.component_health.copy()
        }
        
        return health_status
    
    def set_component_health(self, component: str, is_healthy: bool) -> None:
        """Set health status for a specific component.
        
        Args:
            component: Name of the component (e.g., 'database', 'redis', 'ai_api')
            is_healthy: Health status of the component
        """
        self.component_health[component] = is_healthy
        
        # Update overall health based on all components
        self.is_healthy = all(self.component_health.values()) if self.component_health else True
        
        status = "healthy" if is_healthy else "unhealthy"
        logger.info(f"Component '{component}' marked as {status}")
    
    def set_unhealthy(self, reason: Optional[str] = None) -> None:
        """Mark service as unhealthy.
        
        Args:
            reason: Optional reason for unhealthy status
        """
        self.is_healthy = False
        log_msg = "Service marked as unhealthy"
        if reason:
            log_msg += f": {reason}"
        logger.warning(log_msg)
    
    def set_healthy(self) -> None:
        """Mark service as healthy."""
        self.is_healthy = True
        logger.info("Service marked as healthy")


# Global health check instance
health_check = HealthCheck()


def record_error(category: str, severity: str = 'error') -> None:
    """Record an error in metrics.
    
    Args:
        category: Error category (e.g., 'generation', 'publishing', 'api')
        severity: Error severity level (e.g., 'warning', 'error', 'critical')
    """
    error_count.labels(category=category, severity=severity).inc()
    logger.debug(f"Recorded error: category={category}, severity={severity}")


def update_queue_metrics(channel_id: int, size: int) -> None:
    """Update queue size metrics for a channel.
    
    Args:
        channel_id: Channel identifier
        size: Current queue size
    """
    queue_size.labels(channel_id=str(channel_id)).set(size)


def update_active_channels_count(count: int) -> None:
    """Update the count of active channels.
    
    Args:
        count: Number of currently active channels
    """
    active_channels.set(count)


def update_cache_metrics(backend: str, stats: dict) -> None:
    """Update cache metrics from cache statistics.
    
    Args:
        backend: Cache backend ('redis' or 'memory')
        stats: Cache statistics dictionary
    """
    if 'total_keys' in stats:
        cache_size.labels(backend=backend).set(stats['total_keys'])
    
    if 'hits' in stats:
        cache_hits.labels(backend=backend).inc(stats['hits'])
    
    if 'misses' in stats:
        cache_misses.labels(backend=backend).inc(stats['misses'])
    
    if 'memory_usage_bytes' in stats:
        cache_memory_usage.labels(backend=backend).set(stats['memory_usage_bytes'])


async def metrics_handler(request):
    """Prometheus metrics endpoint."""
    metrics_data = generate_latest()
    return web.Response(
        body=metrics_data,
        content_type='text/plain; version=0.0.4'
    )


async def health_handler(request):
    """Health check endpoint with enhanced status."""
    # Get basic health status
    basic_health = await health_check.check()
    
    # Get enhanced health status if available
    health_service = request.app.get('health_service')
    if health_service:
        try:
            enhanced_status = await health_service.get_health_status()
            health_status = enhanced_status.to_dict()
            
            # Merge with basic health
            health_status['uptime_seconds'] = basic_health['uptime_seconds']
            health_status['basic_components'] = basic_health['components']
        except Exception as e:
            logger.error(f"Error getting enhanced health status: {e}")
            health_status = basic_health
    else:
        health_status = basic_health
    
    if health_status['status'] in ('healthy', 'degraded'):
        return web.json_response(health_status, status=200)
    else:
        return web.json_response(health_status, status=503)


async def start_monitoring_server(port: int = 9090, health_service=None) -> web.AppRunner:
    """Start monitoring HTTP server.
    
    Args:
        port: Port number for the monitoring server (default: 9090)
        health_service: Optional HealthCheckService instance for enhanced health checks
        
    Returns:
        AppRunner instance for graceful shutdown
        
    Raises:
        OSError: If port is already in use
    """
    app = web.Application()
    
    # Store health service in app for access in handlers
    if health_service:
        app['health_service'] = health_service
    
    app.router.add_get('/metrics', metrics_handler)
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    try:
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"Monitoring server started on port {port}")
        return runner
    except OSError as e:
        logger.error(f"Failed to start monitoring server on port {port}: {e}")
        await runner.cleanup()
        raise


async def stop_monitoring_server(runner: web.AppRunner) -> None:
    """Stop monitoring HTTP server gracefully.
    
    Args:
        runner: AppRunner instance to stop
    """
    if runner:
        logger.info("Stopping monitoring server...")
        await runner.cleanup()
        logger.info("Monitoring server stopped")
