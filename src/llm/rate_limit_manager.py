"""
Rate Limit Manager - Sliding window rate limiting with Redis backend
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RateLimitManager:
    """
    Rate Limit Manager using sliding window algorithm.
    
    Features:
    - Per-provider rate limiting
    - Sliding window algorithm for accurate limits
    - Redis backend for distributed systems
    - Automatic reset of counters
    - Statistics tracking
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        use_redis: bool = True
    ):
        """
        Initialize Rate Limit Manager.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            use_redis: Whether to use Redis (falls back to in-memory if False)
        """
        self.use_redis = use_redis and REDIS_AVAILABLE and redis_url
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info("✅ Rate Limit Manager initialized with Redis")
            except Exception as e:
                logger.warning(f"⚠️ Failed to connect to Redis, using in-memory: {e}")
                self.use_redis = False
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info("✅ Rate Limit Manager initialized with in-memory storage")
        
        # In-memory fallback storage
        self.memory_storage: Dict[str, list] = {}
        self.stats: Dict[str, Dict] = {}
    
    async def check_limit(
        self,
        provider_name: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            provider_name: Name of the provider (e.g., "groq", "gemini")
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds (default: 60 for per-minute)
            
        Returns:
            True if within limit, False if limit exceeded
        """
        key = f"ratelimit:{provider_name}:{window_seconds}"
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        if self.use_redis:
            return await self._check_limit_redis(key, now, window_start, limit)
        else:
            return self._check_limit_memory(key, now, window_start, limit)
    
    async def record_request(
        self,
        provider_name: str,
        window_seconds: int = 60
    ):
        """
        Record a request for rate limiting.
        
        Args:
            provider_name: Name of the provider
            window_seconds: Time window in seconds
        """
        key = f"ratelimit:{provider_name}:{window_seconds}"
        now = datetime.utcnow().timestamp()
        
        if self.use_redis:
            await self._record_request_redis(key, now, window_seconds)
        else:
            self._record_request_memory(key, now)
        
        # Update statistics
        self._update_stats(provider_name)
    
    async def get_current_usage(
        self,
        provider_name: str,
        window_seconds: int = 60
    ) -> int:
        """
        Get current request count in window.
        
        Args:
            provider_name: Name of the provider
            window_seconds: Time window in seconds
            
        Returns:
            Number of requests in current window
        """
        key = f"ratelimit:{provider_name}:{window_seconds}"
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        if self.use_redis:
            return await self._get_usage_redis(key, window_start)
        else:
            return self._get_usage_memory(key, window_start)
    
    async def reset_limits(self, provider_name: str):
        """
        Reset all limits for a provider.
        
        Args:
            provider_name: Name of the provider
        """
        if self.use_redis:
            # Delete all keys for this provider
            pattern = f"ratelimit:{provider_name}:*"
            async for key in self.redis_client.scan_iter(match=pattern):
                await self.redis_client.delete(key)
            logger.info(f"Reset Redis rate limits for {provider_name}")
        else:
            # Clear memory storage
            keys_to_delete = [k for k in self.memory_storage.keys() if provider_name in k]
            for key in keys_to_delete:
                del self.memory_storage[key]
            logger.info(f"Reset memory rate limits for {provider_name}")
    
    def get_statistics(self, provider_name: Optional[str] = None) -> Dict:
        """
        Get rate limit statistics.
        
        Args:
            provider_name: Optional provider name to filter stats
            
        Returns:
            Dictionary with statistics
        """
        if provider_name:
            return self.stats.get(provider_name, {
                'total_requests': 0,
                'rate_limited': 0,
                'last_request': None
            })
        else:
            return self.stats.copy()
    
    # Redis implementation
    async def _check_limit_redis(
        self,
        key: str,
        now: float,
        window_start: float,
        limit: int
    ) -> bool:
        """Check limit using Redis sorted set"""
        try:
            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current entries
            count = await self.redis_client.zcard(key)
            
            return count < limit
            
        except Exception as e:
            logger.error(f"Redis check_limit error: {e}")
            # Fallback to allowing request on error
            return True
    
    async def _record_request_redis(self, key: str, now: float, window_seconds: int):
        """Record request using Redis sorted set"""
        try:
            # Add current timestamp
            await self.redis_client.zadd(key, {str(now): now})
            
            # Set expiration to window + buffer
            await self.redis_client.expire(key, window_seconds + 10)
            
        except Exception as e:
            logger.error(f"Redis record_request error: {e}")
    
    async def _get_usage_redis(self, key: str, window_start: float) -> int:
        """Get usage from Redis"""
        try:
            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current entries
            return await self.redis_client.zcard(key)
            
        except Exception as e:
            logger.error(f"Redis get_usage error: {e}")
            return 0
    
    # Memory implementation
    def _check_limit_memory(
        self,
        key: str,
        now: float,
        window_start: float,
        limit: int
    ) -> bool:
        """Check limit using in-memory storage"""
        if key not in self.memory_storage:
            self.memory_storage[key] = []
        
        # Remove old entries
        self.memory_storage[key] = [
            ts for ts in self.memory_storage[key]
            if ts > window_start
        ]
        
        return len(self.memory_storage[key]) < limit
    
    def _record_request_memory(self, key: str, now: float):
        """Record request in memory"""
        if key not in self.memory_storage:
            self.memory_storage[key] = []
        
        self.memory_storage[key].append(now)
    
    def _get_usage_memory(self, key: str, window_start: float) -> int:
        """Get usage from memory"""
        if key not in self.memory_storage:
            return 0
        
        # Remove old entries
        self.memory_storage[key] = [
            ts for ts in self.memory_storage[key]
            if ts > window_start
        ]
        
        return len(self.memory_storage[key])
    
    def _update_stats(self, provider_name: str):
        """Update statistics for provider"""
        if provider_name not in self.stats:
            self.stats[provider_name] = {
                'total_requests': 0,
                'rate_limited': 0,
                'last_request': None
            }
        
        self.stats[provider_name]['total_requests'] += 1
        self.stats[provider_name]['last_request'] = datetime.utcnow().isoformat()
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")
    
    def __str__(self) -> str:
        backend = "Redis" if self.use_redis else "Memory"
        return f"RateLimitManager(backend={backend}, providers={len(self.stats)})"


# Convenience function to create rate limit manager from environment
def create_rate_limit_manager_from_env() -> RateLimitManager:
    """
    Create Rate Limit Manager from environment variables.
    
    Returns:
        RateLimitManager instance
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    use_redis = os.getenv("LLM_USE_REDIS", "true").lower() == "true"
    
    try:
        manager = RateLimitManager(redis_url=redis_url, use_redis=use_redis)
        logger.info("✅ Rate Limit Manager created from environment")
        return manager
    except Exception as e:
        logger.error(f"❌ Failed to create Rate Limit Manager: {e}")
        # Return in-memory fallback
        return RateLimitManager(use_redis=False)
