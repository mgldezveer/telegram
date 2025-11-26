"""Health check service for monitoring system components."""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ComponentStatus:
    """Status of a system component.
    
    Attributes:
        name: Component name
        status: Status ('healthy', 'degraded', 'unhealthy')
        message: Status message
        details: Additional details (optional)
    """
    name: str
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class HealthStatus:
    """Overall system health status.
    
    Attributes:
        status: Overall status ('healthy', 'degraded', 'unhealthy')
        components: Dictionary of component statuses
        timestamp: When health check was performed
    """
    status: str
    components: Dict[str, ComponentStatus]
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
            'components': {
                name: {
                    'status': comp.status,
                    'message': comp.message,
                    'details': comp.details
                }
                for name, comp in self.components.items()
            }
        }


class HealthCheckService:
    """System health monitoring service.
    
    This service monitors the health of various system components
    including cache (Redis/memory), database, and other services.
    """
    
    def __init__(self, cache_service=None):
        """Initialize health check service.
        
        Args:
            cache_service: Cache service instance to monitor
        """
        self.cache_service = cache_service
        self._start_time = datetime.now()
        self._check_count = 0
        self._last_check: Optional[datetime] = None
    
    async def get_health_status(self) -> HealthStatus:
        """Get overall system health status.
        
        Returns:
            HealthStatus with all component statuses
        """
        self._check_count += 1
        self._last_check = datetime.now()
        
        components = {}
        
        # Check cache status
        if self.cache_service:
            components['cache'] = await self._check_cache_health()
        
        # Determine overall status
        overall_status = self._determine_overall_status(components)
        
        return HealthStatus(
            status=overall_status,
            components=components,
            timestamp=self._last_check
        )
    
    async def _check_cache_health(self) -> ComponentStatus:
        """Check cache health.
        
        Returns:
            ComponentStatus for cache
        """
        try:
            cache_health = await self.cache_service.health_check()
            
            if cache_health.get('healthy', False):
                backend = cache_health.get('backend', 'unknown')
                
                if backend == 'redis':
                    redis_info = cache_health.get('redis_info', {})
                    return ComponentStatus(
                        name='cache',
                        status='healthy',
                        message=f'Redis connected (v{redis_info.get("version", "unknown")})',
                        details={
                            'backend': 'redis',
                            'redis_version': redis_info.get('version'),
                            'uptime_seconds': redis_info.get('uptime_seconds'),
                            'connected_clients': redis_info.get('connected_clients'),
                            'memory_usage': redis_info.get('used_memory_human')
                        }
                    )
                elif backend == 'memory':
                    stats = cache_health.get('memory_cache_stats', {})
                    return ComponentStatus(
                        name='cache',
                        status='degraded',
                        message='Using memory cache fallback (Redis unavailable)',
                        details={
                            'backend': 'memory',
                            'total_keys': stats.get('total_keys', 0),
                            'hit_rate': stats.get('hit_rate', 0),
                            'memory_usage_mb': stats.get('memory_usage_mb', 0)
                        }
                    )
            
            return ComponentStatus(
                name='cache',
                status='unhealthy',
                message='Cache not available',
                details=cache_health
            )
            
        except Exception as e:
            logger.error(f"Error checking cache health: {e}")
            return ComponentStatus(
                name='cache',
                status='unhealthy',
                message=f'Health check failed: {str(e)}',
                details={'error': str(e)}
            )
    
    async def get_redis_status(self) -> Dict[str, Any]:
        """Get Redis-specific status.
        
        Returns:
            Dictionary with Redis status information
        """
        if not self.cache_service:
            return {
                'available': False,
                'message': 'Cache service not configured'
            }
        
        try:
            cache_health = await self.cache_service.health_check()
            
            return {
                'available': cache_health.get('redis_available', False),
                'backend': cache_health.get('backend', 'unknown'),
                'fallback_active': cache_health.get('fallback_active', False),
                'connection_attempts': cache_health.get('connection_attempts', 0),
                'last_attempt': cache_health.get('last_attempt'),
                'redis_info': cache_health.get('redis_info'),
                'memory_cache_stats': cache_health.get('memory_cache_stats')
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis status: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    def _determine_overall_status(self, components: Dict[str, ComponentStatus]) -> str:
        """Determine overall system status from component statuses.
        
        Args:
            components: Dictionary of component statuses
            
        Returns:
            Overall status ('healthy', 'degraded', 'unhealthy')
        """
        if not components:
            return 'unhealthy'
        
        statuses = [comp.status for comp in components.values()]
        
        # If any component is unhealthy, system is unhealthy
        if 'unhealthy' in statuses:
            return 'unhealthy'
        
        # If any component is degraded, system is degraded
        if 'degraded' in statuses:
            return 'degraded'
        
        # All components healthy
        return 'healthy'
    
    def get_service_info(self) -> dict:
        """Get health check service information.
        
        Returns:
            Dictionary with service information
        """
        uptime = datetime.now() - self._start_time
        
        return {
            'service': 'health_check',
            'uptime_seconds': int(uptime.total_seconds()),
            'check_count': self._check_count,
            'last_check': self._last_check.isoformat() if self._last_check else None,
            'monitored_components': ['cache']
        }
