"""
Cache Service - LLM response caching with Redis and LRU fallback
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache implementation for fallback"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl_map: Dict[str, datetime] = {}
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        # Check TTL
        if key in self.ttl_map:
            if datetime.utcnow() > self.ttl_map[key]:
                # Expired
                self.cache.pop(key, None)
                self.ttl_map.pop(key, None)
                return None
        
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        
        return None
    
    def set(self, key: str, value: str, ttl_seconds: int = 3600):
        """Set value in cache with TTL"""
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            self.cache[key] = value
            
            # Evict oldest if over limit
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.ttl_map.pop(oldest_key, None)
        
        # Set TTL
        self.ttl_map[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.ttl_map.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class CacheService:
    """
    Cache Service for LLM responses.
    
    Features:
    - Redis backend with LRU fallback
    - Automatic cache key generation from prompts
    - TTL support
    - Optional semantic caching (similar prompts)
    - Statistics tracking
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        use_redis: bool = True,
        default_ttl: int = 3600,
        max_memory_size: int = 1000
    ):
        """
        Initialize Cache Service.
        
        Args:
            redis_url: Redis connection URL
            use_redis: Whether to use Redis (falls back to LRU if False)
            default_ttl: Default TTL in seconds (default: 1 hour)
            max_memory_size: Max size for LRU cache
        """
        self.default_ttl = default_ttl
        self.use_redis = use_redis and REDIS_AVAILABLE and redis_url
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info("✅ Cache Service initialized with Redis")
            except Exception as e:
                logger.warning(f"⚠️ Failed to connect to Redis, using LRU: {e}")
                self.use_redis = False
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info("✅ Cache Service initialized with LRU cache")
        
        # LRU fallback
        self.lru_cache = LRUCache(max_size=max_memory_size)
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    def generate_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate cache key from prompt parameters.
        
        Args:
            prompt: User prompt
            model: Model name
            temperature: Temperature setting
            max_tokens: Max tokens setting
            system_prompt: Optional system prompt
            
        Returns:
            Cache key (hash)
        """
        # Create deterministic string from parameters
        cache_data = {
            'prompt': prompt,
            'model': model,
            'temperature': round(temperature, 2),  # Round to avoid float precision issues
            'max_tokens': max_tokens,
            'system_prompt': system_prompt or ''
        }
        
        # Generate hash
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()
        
        return f"llm_cache:{cache_hash}"
    
    async def get(self, cache_key: str) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if self.use_redis:
            value = await self._get_redis(cache_key)
        else:
            value = self.lru_cache.get(cache_key)
        
        if value:
            self.stats['hits'] += 1
            logger.debug(f"Cache HIT: {cache_key[:16]}...")
        else:
            self.stats['misses'] += 1
            logger.debug(f"Cache MISS: {cache_key[:16]}...")
        
        return value
    
    async def set(
        self,
        cache_key: str,
        value: str,
        ttl: Optional[int] = None
    ):
        """
        Set value in cache.
        
        Args:
            cache_key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        
        if self.use_redis:
            await self._set_redis(cache_key, value, ttl)
        else:
            self.lru_cache.set(cache_key, value, ttl)
        
        self.stats['sets'] += 1
        logger.debug(f"Cache SET: {cache_key[:16]}... (TTL: {ttl}s)")
    
    async def delete(self, cache_key: str):
        """
        Delete value from cache.
        
        Args:
            cache_key: Cache key
        """
        if self.use_redis:
            await self.redis_client.delete(cache_key)
        else:
            self.lru_cache.cache.pop(cache_key, None)
            self.lru_cache.ttl_map.pop(cache_key, None)
        
        logger.debug(f"Cache DELETE: {cache_key[:16]}...")
    
    async def clear(self):
        """Clear all cache"""
        if self.use_redis:
            # Delete all llm_cache keys
            async for key in self.redis_client.scan_iter(match="llm_cache:*"):
                await self.redis_client.delete(key)
            logger.info("Cleared Redis cache")
        else:
            self.lru_cache.clear()
            logger.info("Cleared LRU cache")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'backend': 'Redis' if self.use_redis else 'LRU',
            'size': self.lru_cache.size() if not self.use_redis else 'N/A'
        }
    
    # Redis implementation
    async def _get_redis(self, key: str) -> Optional[str]:
        """Get from Redis"""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def _set_redis(self, key: str, value: str, ttl: int):
        """Set in Redis with TTL"""
        try:
            await self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"CacheService(backend={stats['backend']}, hit_rate={stats['hit_rate']}%, size={stats.get('size', 'N/A')})"


# Convenience function to create cache service from environment
def create_cache_service_from_env() -> CacheService:
    """
    Create Cache Service from environment variables.
    
    Returns:
        CacheService instance
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    use_redis = os.getenv("LLM_USE_REDIS", "true").lower() == "true"
    default_ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))
    max_memory_size = int(os.getenv("LLM_CACHE_MAX_SIZE", "1000"))
    
    try:
        service = CacheService(
            redis_url=redis_url,
            use_redis=use_redis,
            default_ttl=default_ttl,
            max_memory_size=max_memory_size
        )
        logger.info("✅ Cache Service created from environment")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to create Cache Service: {e}")
        # Return LRU fallback
        return CacheService(use_redis=False)
