"""Unit tests for cache service."""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.cache.memory_cache import MemoryCache, CacheEntry
from src.cache.cache_service import CacheService, ConnectionResult


class TestMemoryCache:
    """Test MemoryCache functionality."""
    
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = MemoryCache(max_size=10, default_ttl=300)
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        cache = MemoryCache()
        result = await cache.get("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = MemoryCache(default_ttl=1)  # 1 second TTL
        
        await cache.set("key1", "value1", ttl=1)
        
        # Should exist immediately
        result = await cache.get("key1")
        assert result == "value1"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting entries."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        assert await cache.exists("key1")
        
        deleted = await cache.delete("key1")
        assert deleted is True
        assert not await cache.exists("key1")
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        """Test deleting non-existent key."""
        cache = MemoryCache()
        
        deleted = await cache.delete("nonexistent")
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking key existence."""
        cache = MemoryCache()
        
        assert not await cache.exists("key1")
        
        await cache.set("key1", "value1")
        assert await cache.exists("key1")
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = MemoryCache(max_size=3)
        
        # Fill cache
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # All should exist
        assert await cache.exists("key1")
        assert await cache.exists("key2")
        assert await cache.exists("key3")
        
        # Add one more - should evict oldest (key1)
        await cache.set("key4", "value4")
        
        assert not await cache.exists("key1")  # Evicted
        assert await cache.exists("key2")
        assert await cache.exists("key3")
        assert await cache.exists("key4")
    
    @pytest.mark.asyncio
    async def test_update_existing_key(self):
        """Test updating existing key."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        await cache.set("key1", "value2")
        
        result = await cache.get("key1")
        assert result == "value2"
    
    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing all entries."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert not await cache.exists("key1")
        assert not await cache.exists("key2")
        assert len(cache) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = MemoryCache(default_ttl=1)
        
        await cache.set("key1", "value1", ttl=1)
        await cache.set("key2", "value2", ttl=10)
        
        # Wait for key1 to expire
        await asyncio.sleep(1.1)
        
        # Cleanup
        removed = await cache.cleanup_expired()
        
        assert removed == 1
        assert not await cache.exists("key1")
        assert await cache.exists("key2")
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting cache statistics."""
        cache = MemoryCache(max_size=100, default_ttl=300)
        
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        
        assert stats['backend'] == 'memory'
        assert stats['total_keys'] == 1
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['max_size'] == 100
        assert stats['default_ttl'] == 300
    
    @pytest.mark.asyncio
    async def test_get_all_keys(self):
        """Test getting all keys."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        keys = await cache.get_all_keys()
        
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys
    
    @pytest.mark.asyncio
    async def test_complex_values(self):
        """Test storing complex values."""
        cache = MemoryCache()
        
        # Dictionary
        await cache.set("dict", {"a": 1, "b": 2})
        result = await cache.get("dict")
        assert result == {"a": 1, "b": 2}
        
        # List
        await cache.set("list", [1, 2, 3])
        result = await cache.get("list")
        assert result == [1, 2, 3]
        
        # Nested
        await cache.set("nested", {"list": [1, 2], "dict": {"x": "y"}})
        result = await cache.get("nested")
        assert result == {"list": [1, 2], "dict": {"x": "y"}}


class TestCacheEntry:
    """Test CacheEntry functionality."""
    
    def test_is_expired(self):
        """Test expiration checking."""
        now = datetime.now()
        
        # Not expired
        entry = CacheEntry(
            key="key1",
            value="value1",
            created_at=now,
            expires_at=now + timedelta(seconds=10)
        )
        assert not entry.is_expired()
        
        # Expired
        entry = CacheEntry(
            key="key2",
            value="value2",
            created_at=now - timedelta(seconds=20),
            expires_at=now - timedelta(seconds=10)
        )
        assert entry.is_expired()
    
    def test_increment_hits(self):
        """Test hit counter increment."""
        entry = CacheEntry(
            key="key1",
            value="value1",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=10)
        )
        
        assert entry.hit_count == 0
        
        entry.increment_hits()
        assert entry.hit_count == 1
        
        entry.increment_hits()
        assert entry.hit_count == 2


class TestCacheService:
    """Test CacheService functionality."""
    
    @pytest.mark.asyncio
    async def test_fallback_activation(self):
        """Test fallback to memory cache when Redis unavailable."""
        # Use invalid Redis URL to force fallback
        cache = CacheService(fallback_enabled=True)
        
        # Mock config to use invalid URL
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            result = await cache.connect()
            
            assert result.success is True
            assert result.backend == 'memory'
            assert cache.fallback_cache is not None
            assert not cache.is_redis_available
        finally:
            config_module.config.redis.url = original_url
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_fallback_operations(self):
        """Test cache operations with fallback."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            await cache.connect()
            
            # Test operations
            await cache.set("key1", "value1")
            result = await cache.get("key1")
            assert result == "value1"
            
            assert await cache.exists("key1")
            
            await cache.delete("key1")
            assert not await cache.exists("key1")
        finally:
            config_module.config.redis.url = original_url
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_health_check_with_fallback(self):
        """Test health check with memory fallback."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            await cache.connect()
            
            health = await cache.health_check()
            
            assert health['backend'] == 'memory'
            assert not health['redis_available']
            assert health['fallback_active']
            assert 'memory_cache_stats' in health
        finally:
            config_module.config.redis.url = original_url
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_get_stats_with_fallback(self):
        """Test getting stats with memory fallback."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            await cache.connect()
            
            await cache.set("key1", "value1")
            await cache.get("key1")
            
            stats = cache.get_stats()
            
            assert stats is not None
            assert stats.backend == 'memory'
            assert stats.total_keys >= 0
        finally:
            config_module.config.redis.url = original_url
            await cache.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
