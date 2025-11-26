"""Cache module with Redis and memory fallback support."""

from src.cache.cache_service import CacheService, ConnectionResult, CacheStats

# Global cache instance
cache = CacheService()

__all__ = ['cache', 'CacheService', 'ConnectionResult', 'CacheStats']
