# Performance Optimization

## Async Best Practices

- Use async/await for all I/O operations
- Avoid blocking calls in async functions
- Use connection pooling for databases
- Implement caching for frequently accessed data

## Caching

```python
from functools import lru_cache
import asyncio

# Simple in-memory cache
@lru_cache(maxsize=128)
def get_static_data(key: str):
    """Cache static data."""
    return expensive_operation(key)

# Async cache with TTL
class AsyncCache:
    def __init__(self, ttl: int = 300):
        self._cache = {}
        self._ttl = ttl
    
    async def get(self, key: str):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
        return None
    
    async def set(self, key: str, value):
        self._cache[key] = (value, time.time())
```

## Rate Limiting

Implement rate limiting to prevent abuse:

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window)
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        now = datetime.now()
        cutoff = now - self.window
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
```

## Database Optimization

- Use indexes on frequently queried columns
- Implement connection pooling
- Use batch operations when possible
- Avoid N+1 queries
- Use database-level caching (Redis)

## Message Processing

- Process messages asynchronously
- Use queues for heavy operations
- Implement timeouts for external API calls
- Batch similar operations

## Monitoring Performance

```python
import time
from functools import wraps

def measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

## Resource Limits

- Set memory limits for containers
- Implement request timeouts
- Limit concurrent operations
- Monitor and log resource usage
