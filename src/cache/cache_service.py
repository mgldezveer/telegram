"""Enhanced cache service with Redis and memory fallback."""

import logging
import json
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis

from src.config import config
from src.cache.memory_cache import MemoryCache

logger = logging.getLogger(__name__)


@dataclass
class ConnectionResult:
    """Result of cache connection attempt.
    
    Attributes:
        success: Whether connection was successful
        backend: Backend being used ('redis' or 'memory')
        message: Human-readable message
        error: Exception if connection failed
    """
    success: bool
    backend: str
    message: str
    error: Optional[Exception] = None


@dataclass
class CacheStats:
    """Cache statistics.
    
    Attributes:
        backend: Current backend ('redis' or 'memory')
        total_keys: Total number of keys
        hit_rate: Cache hit rate percentage
        miss_rate: Cache miss rate percentage
        memory_usage: Memory usage in bytes (None for Redis)
        uptime: Cache uptime
    """
    backend: str
    total_keys: int
    hit_rate: float
    miss_rate: float
    memory_usage: Optional[int]
    uptime: timedelta


class CacheService:
    """Enhanced caching service with automatic fallback.
    
    This service attempts to use Redis for caching, but automatically
    falls back to an in-memory cache if Redis is unavailable.
    """
    
    def __init__(self, fallback_enabled: bool = True, reconnect_interval: int = 60):
        """Initialize cache service.
        
        Args:
            fallback_enabled: Whether to enable memory cache fallback
            reconnect_interval: Seconds between reconnection attempts
        """
        self.redis: Optional[redis.Redis] = None
        self.fallback_cache: Optional[MemoryCache] = None
        self.is_redis_available: bool = False
        self.fallback_enabled = fallback_enabled
        self.default_ttl = 300  # 5 minutes
        self._connection_attempts = 0
        self._last_connection_attempt: Optional[datetime] = None
        self._reconnect_interval = reconnect_interval
        self._reconnect_task: Optional[Any] = None
    
    async def connect(self) -> ConnectionResult:
        """Connect to Redis with automatic fallback to memory cache.
        
        Returns:
            ConnectionResult indicating success and backend used
        """
        self._connection_attempts += 1
        self._last_connection_attempt = datetime.now()
        
        try:
            # Attempt Redis connection
            logger.info("Attempting to connect to Redis...")
            self.redis = redis.from_url(
                config.redis.url,
                max_connections=config.redis.max_connections,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            self.is_redis_available = True
            
            logger.info("✅ Connected to Redis successfully")
            return ConnectionResult(
                success=True,
                backend='redis',
                message='Connected to Redis successfully'
            )
            
        except redis.ConnectionError as e:
            logger.warning(f"⚠️  Redis connection failed: {e}")
            return await self._activate_fallback(e)
            
        except redis.TimeoutError as e:
            logger.warning(f"⚠️  Redis connection timeout: {e}")
            return await self._activate_fallback(e)
            
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Redis: {e}")
            return await self._activate_fallback(e)
    
    async def _activate_fallback(self, error: Exception) -> ConnectionResult:
        """Activate memory cache fallback.
        
        Args:
            error: Exception that caused fallback activation
            
        Returns:
            ConnectionResult for fallback activation
        """
        if not self.fallback_enabled:
            logger.error("Fallback cache is disabled, cannot continue")
            return ConnectionResult(
                success=False,
                backend='none',
                message='Redis unavailable and fallback disabled',
                error=error
            )
        
        logger.info("Activating memory cache fallback...")
        self.fallback_cache = MemoryCache(
            max_size=1000,
            default_ttl=self.default_ttl
        )
        self.is_redis_available = False
        
        logger.info("✅ Memory cache fallback activated")
        return ConnectionResult(
            success=True,
            backend='memory',
            message='Using memory cache (Redis unavailable)',
            error=error
        )
    
    async def close(self) -> None:
        """Close cache connections and stop reconnection task."""
        # Stop reconnection task
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            logger.info("Reconnection task stopped")
        
        if self.redis:
            try:
                await self.redis.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        
        if self.fallback_cache:
            await self.fallback_cache.clear()
            logger.info("Memory cache cleared")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or fallback).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if self.is_redis_available and self.redis:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
                return None
            elif self.fallback_cache:
                return await self.fallback_cache.get(key)
            else:
                logger.warning("No cache backend available")
                return None
                
        except redis.ConnectionError:
            logger.warning("Redis connection lost, switching to fallback")
            await self._handle_redis_failure()
            return await self.get(key)  # Retry with fallback
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache (Redis or fallback).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            ttl = ttl or self.default_ttl
            
            if self.is_redis_available and self.redis:
                serialized = json.dumps(value)
                await self.redis.setex(key, ttl, serialized)
            elif self.fallback_cache:
                await self.fallback_cache.set(key, value, ttl)
            else:
                logger.warning("No cache backend available")
                
        except redis.ConnectionError:
            logger.warning("Redis connection lost, switching to fallback")
            await self._handle_redis_failure()
            await self.set(key, value, ttl)  # Retry with fallback
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        try:
            if self.is_redis_available and self.redis:
                result = await self.redis.delete(key)
                return result > 0
            elif self.fallback_cache:
                return await self.fallback_cache.delete(key)
            else:
                return False
                
        except redis.ConnectionError:
            logger.warning("Redis connection lost, switching to fallback")
            await self._handle_redis_failure()
            return await self.delete(key)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            if self.is_redis_available and self.redis:
                return await self.redis.exists(key) > 0
            elif self.fallback_cache:
                return await self.fallback_cache.exists(key)
            else:
                return False
                
        except redis.ConnectionError:
            logger.warning("Redis connection lost, switching to fallback")
            await self._handle_redis_failure()
            return await self.exists(key)
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def _handle_redis_failure(self) -> None:
        """Handle Redis connection failure by activating fallback."""
        if self.is_redis_available:
            self.is_redis_available = False
            logger.warning("Redis connection failed, activating fallback")
            
            if not self.fallback_cache and self.fallback_enabled:
                self.fallback_cache = MemoryCache(
                    max_size=1000,
                    default_ttl=self.default_ttl
                )
                logger.info("Memory cache fallback activated")
    
    async def health_check(self) -> dict:
        """Check cache health and return status.
        
        Returns:
            Dictionary with health status information
        """
        status = {
            'backend': 'redis' if self.is_redis_available else 'memory',
            'redis_available': self.is_redis_available,
            'fallback_enabled': self.fallback_enabled,
            'fallback_active': self.fallback_cache is not None,
            'connection_attempts': self._connection_attempts,
            'last_attempt': self._last_connection_attempt.isoformat() if self._last_connection_attempt else None
        }
        
        try:
            if self.is_redis_available and self.redis:
                # Get Redis info
                info = await self.redis.info()
                status['redis_info'] = {
                    'version': info.get('redis_version'),
                    'uptime_seconds': info.get('uptime_in_seconds'),
                    'connected_clients': info.get('connected_clients'),
                    'used_memory_human': info.get('used_memory_human')
                }
                status['healthy'] = True
            elif self.fallback_cache:
                # Get memory cache stats
                stats = self.fallback_cache.get_stats()
                status['memory_cache_stats'] = stats
                status['healthy'] = True
            else:
                status['healthy'] = False
                status['message'] = 'No cache backend available'
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
            status['healthy'] = False
            status['error'] = str(e)
        
        return status
    
    def get_stats(self) -> Optional[CacheStats]:
        """Get cache statistics.
        
        Returns:
            CacheStats object or None if no backend available
        """
        try:
            if self.fallback_cache:
                stats = self.fallback_cache.get_stats()
                return CacheStats(
                    backend='memory',
                    total_keys=stats['total_keys'],
                    hit_rate=stats['hit_rate'],
                    miss_rate=stats['miss_rate'],
                    memory_usage=stats['memory_usage_bytes'],
                    uptime=timedelta(seconds=stats['uptime_seconds'])
                )
            # Redis stats would require additional tracking
            return None
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return None
    
    async def start_reconnection_task(self) -> None:
        """Start background task for Redis reconnection attempts."""
        if not self.is_redis_available and self.fallback_cache:
            logger.info("Starting Redis reconnection task...")
            self._reconnect_task = asyncio.create_task(self._reconnection_loop())
    
    async def _reconnection_loop(self) -> None:
        """Background loop for attempting Redis reconnection."""
        while not self.is_redis_available:
            try:
                await asyncio.sleep(self._reconnect_interval)
                
                logger.info("Attempting to reconnect to Redis...")
                result = await self._try_reconnect()
                
                if result.success and result.backend == 'redis':
                    logger.info("✅ Successfully reconnected to Redis")
                    # Migrate data from memory cache if needed
                    await self._migrate_to_redis()
                    break
                else:
                    logger.debug(f"Reconnection attempt failed, will retry in {self._reconnect_interval}s")
                    
            except asyncio.CancelledError:
                logger.info("Reconnection task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in reconnection loop: {e}")
    
    async def _try_reconnect(self) -> ConnectionResult:
        """Try to reconnect to Redis.
        
        Returns:
            ConnectionResult indicating success or failure
        """
        try:
            # Close existing connection if any
            if self.redis:
                try:
                    await self.redis.close()
                except:
                    pass
            
            # Attempt new connection
            self.redis = redis.from_url(
                config.redis.url,
                max_connections=config.redis.max_connections,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            self.is_redis_available = True
            
            return ConnectionResult(
                success=True,
                backend='redis',
                message='Reconnected to Redis successfully'
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                backend='memory',
                message=f'Reconnection failed: {str(e)}',
                error=e
            )
    
    async def _migrate_to_redis(self) -> None:
        """Migrate data from memory cache to Redis after reconnection."""
        if not self.fallback_cache or not self.is_redis_available:
            return
        
        try:
            logger.info("Migrating data from memory cache to Redis...")
            keys = await self.fallback_cache.get_all_keys()
            migrated = 0
            
            for key in keys:
                try:
                    value = await self.fallback_cache.get(key)
                    if value is not None:
                        # Use default TTL for migrated data
                        await self.set(key, value, self.default_ttl)
                        migrated += 1
                except Exception as e:
                    logger.warning(f"Failed to migrate key {key}: {e}")
            
            logger.info(f"Migrated {migrated}/{len(keys)} keys to Redis")
            
            # Clear memory cache after successful migration
            await self.fallback_cache.clear()
            self.fallback_cache = None
            
        except Exception as e:
            logger.error(f"Error during cache migration: {e}")
