"""MultiLevelCache demonstration."""

import asyncio
import time
import sys
import os

# Add path to src for module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cache.multi_level_cache import MultiLevelCache, CacheLevel
from src.cache.memory_cache import MemoryCache
from src.cache.redis_cache import RedisCache


async def example_basic_usage():
    """Example of basic MultiLevelCache usage."""
    print("=== Basic MultiLevelCache Usage Example ===")
    
    # Create multi-level cache with two levels: Redis (priority 0) -> Memory (priority 1)
    cache = MultiLevelCache()
    await cache.initialize()
    
    # Set a value
    await cache.set("example_key", "Hello, MultiLevel Cache!", ttl=300)
    
    # Get the value
    value = await cache.get("example_key")
    print(f"Retrieved value: {value}")
    
    # Check if key exists
    exists = await cache.exists("example_key")
    print(f"Key exists: {exists}")
    
    # Delete the value
    await cache.delete("example_key")
    
    # Check that the value is deleted
    value = await cache.get("example_key")
    print(f"Value after deletion: {value}")
    
    await cache.close()


async def example_custom_levels():
    """Example of using custom cache levels."""
    print("\n=== Custom Cache Levels Example ===")
    
    # Create caches for different levels
    fast_cache = MemoryCache(max_size=100, default_ttl=60)
    slow_cache = MemoryCache(max_size=100, default_ttl=300)
    
    # Define levels: fast (priority 0) -> slow (priority 1)
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=60),
        CacheLevel("slow", slow_cache, 1, default_ttl=300)
    ]
    
    # Create multi-level cache with custom levels
    cache = MultiLevelCache(levels=levels, sync_strategy="write_through")
    
    # Initialize cache (starts cleanup task for MemoryCache)
    await cache.initialize()
    
    # Set a value
    await cache.set("custom_key", "Custom Level Value", ttl=120)
    
    # Get the value
    value = await cache.get("custom_key")
    print(f"Value from custom cache: {value}")
    
    # Check level status
    level_status = cache.get_level_status()
    print(f"Level status: {level_status}")
    
    await cache.close()


async def example_different_sync_strategies():
    """Example of different synchronization strategies."""
    print("\n=== Different Synchronization Strategies Example ===")
    
    # Create cache levels
    l1_cache = MemoryCache(max_size=50, default_ttl=60)
    l2_cache = MemoryCache(max_size=200, default_ttl=300)
    
    levels = [
        CacheLevel("L1", l1_cache, 0, default_ttl=60),
        CacheLevel("L2", l2_cache, 1, default_ttl=300)
    ]
    
    # Test write-through strategy
    print("\n--- Write-through strategy ---")
    wt_cache = MultiLevelCache(levels=levels.copy(), sync_strategy="write_through")
    await wt_cache.initialize()
    
    await wt_cache.set("wt_key", "Write-through Value", ttl=120)
    
    # Value should be in both levels
    l1_value = await l1_cache.get("wt_key")
    l2_value = await l2_cache.get("wt_key")
    print(f"L1 value: {l1_value}")
    print(f"L2 value: {l2_value}")
    
    await wt_cache.close()
    
    # Test write-back strategy
    print("\n--- Write-back strategy ---")
    wb_cache = MultiLevelCache(levels=levels.copy(), sync_strategy="write_back")
    await wb_cache.initialize()
    
    await wb_cache.set("wb_key", "Write-back Value", ttl=120)
    
    # Value should be only in L1 (fastest level)
    l1_value = await l1_cache.get("wb_key")
    l2_value = await l2_cache.get("wb_key")
    print(f"L1 value: {l1_value}")
    print(f"L2 value: {l2_value}")
    
    await wb_cache.close()


async def example_hash_operations():
    """Example of hash operations."""
    print("\n=== Hash Operations Example ===")
    
    cache = MultiLevelCache()
    await cache.initialize()
    
    # Work with hashes
    await cache.hset("user_profile", "name", "John Doe", ttl=300)
    await cache.hset("user_profile", "email", "john@example.com", ttl=300)
    await cache.hset("user_profile", "age", 30, ttl=300)
    
    # Get individual fields
    name = await cache.hget("user_profile", "name")
    email = await cache.hget("user_profile", "email")
    age = await cache.hget("user_profile", "age")
    
    print(f"Name: {name}, Email: {email}, Age: {age}")
    
    # Get all fields
    profile = await cache.hgetall("user_profile")
    print(f"Full profile: {profile}")
    
    # Delete a field
    deleted = await cache.hdel("user_profile", "email")
    print(f"Fields deleted: {deleted}")
    
    # Check that field is deleted
    email = await cache.hget("user_profile", "email")
    print(f"Email after deletion: {email}")
    
    await cache.close()


async def example_performance_comparison():
    """Example of performance comparison between levels."""
    print("\n=== Performance Comparison Example ===")
    
    # Create cache with different levels
    fast_cache = MemoryCache(max_size=1000, default_ttl=60)
    slow_cache = MemoryCache(max_size=1000, default_ttl=600)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=60),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Set many values in slow level
    for i in range(100):
        await slow_cache.set(f"slow_key_{i}", f"slow_value_{i}", ttl=600)
    
    # Measure access time to values
    start_time = time.time()
    for i in range(100):
        value = await cache.get(f"slow_key_{i}")
        # After first access, value will be cached in fast level
    end_time = time.time()
    
    print(f"Time to access 100 values (including caching): {end_time - start_time:.4f} seconds")
    
    # Now get values again - they should be in fast cache
    start_time = time.time()
    for i in range(100):
        value = await cache.get(f"slow_key_{i}")
    end_time = time.time()
    
    print(f"Time to access 100 values (from fast cache): {end_time - start_time:.4f} seconds")
    
    await cache.close()


async def main():
    """Main example function."""
    print("MultiLevel Cache Demonstration")
    
    await example_basic_usage()
    await example_custom_levels()
    await example_different_sync_strategies()
    await example_hash_operations()
    await example_performance_comparison()
    
    print("\nAll examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())