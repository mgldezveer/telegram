# Caching Strategies

## Redis Cache

```python
import redis.asyncio as redis
import json

class RedisCache:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
    
    async def get(self, key: str):
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        await self.redis.delete(key)
    
    async def close(self):
        await self.redis.close()

cache = RedisCache()
```

## Cache Decorator

```python
from functools import wraps

def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

@cached(ttl=600)
async def get_user_data(user_id: int):
    return await db.get_user(user_id)
```

## In-Memory Cache

```python
from cachetools import TTLCache
import asyncio

class MemoryCache:
    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = asyncio.Lock()
    
    async def get(self, key: str):
        async with self.lock:
            return self.cache.get(key)
    
    async def set(self, key: str, value):
        async with self.lock:
            self.cache[key] = value
```
