"""In-memory cache with TTL support as fallback for Redis."""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Any, Dict
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata.
    
    Attributes:
        key: Cache key
        value: Cached value
        created_at: When entry was created
        expires_at: When entry expires
        hit_count: Number of times entry was accessed
    """
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired.
        
        Returns:
            True if entry has expired
        """
        return datetime.now() > self.expires_at
    
    def increment_hits(self) -> None:
        """Increment hit counter."""
        self.hit_count += 1


class MemoryCache:
    """In-memory cache with TTL and LRU eviction support.
    
    This cache is used as a fallback when Redis is unavailable.
    It implements LRU (Least Recently Used) eviction when the cache
    reaches its maximum size.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default TTL in seconds
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._created_at = datetime.now()
        
        logger.info(f"MemoryCache initialized (max_size={max_size}, default_ttl={default_ttl}s)")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache entry expired: {key}")
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.increment_hits()
            self._hits += 1
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        async with self._lock:
            ttl = ttl or self._default_ttl
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl)
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=expires_at
            )
            
            # If key exists, update it
            if key in self._cache:
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            # Evict oldest entry if cache is full
            if len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1
                logger.debug(f"Evicted oldest entry: {oldest_key}")
    
    async def delete(self, key: str) -> bool:
        """Delete value from memory cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and is not expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return False
            
            if entry.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    async def clear(self) -> None:
        """Clear all entries from cache."""
        async with self._lock:
            self._cache.clear()
            logger.info("Memory cache cleared")
    
    async def cleanup_expired(self) -> int:
        """Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            # Optimize: collect keys first, then delete
            # This is faster than checking during iteration
            expired_keys = []
            now = datetime.now()
            
            for key, entry in self._cache.items():
                if entry.expires_at <= now:
                    expired_keys.append(key)
            
            # Batch delete
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        miss_rate = (self._misses / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate memory usage (approximate)
        memory_bytes = 0
        for entry in self._cache.values():
            try:
                # Approximate size of serialized value
                memory_bytes += len(json.dumps(entry.value))
            except (TypeError, ValueError):
                # If value can't be serialized, estimate size
                memory_bytes += 1024  # 1KB estimate
        
        uptime = datetime.now() - self._created_at
        
        return {
            'backend': 'memory',
            'total_keys': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': round(hit_rate, 2),
            'miss_rate': round(miss_rate, 2),
            'evictions': self._evictions,
            'memory_usage_bytes': memory_bytes,
            'memory_usage_mb': round(memory_bytes / 1024 / 1024, 2),
            'uptime_seconds': int(uptime.total_seconds()),
            'default_ttl': self._default_ttl
        }
    
    async def get_all_keys(self) -> list[str]:
        """Get all non-expired keys in cache.
        
        Returns:
            List of cache keys
        """
        async with self._lock:
            # Clean up expired entries first
            await self.cleanup_expired()
            return list(self._cache.keys())
    
    def __len__(self) -> int:
        """Get number of entries in cache.
        
        Returns:
            Number of cache entries
        """
        return len(self._cache)
