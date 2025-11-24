# Rate Limiting

## Token Bucket Algorithm

```python
import time
from collections import defaultdict

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = defaultdict(lambda: {
            'tokens': capacity,
            'last_refill': time.time()
        })
    
    def consume(self, user_id: int, tokens: int = 1) -> bool:
        bucket = self.buckets[user_id]
        now = time.time()
        
        # Refill tokens
        elapsed = now - bucket['last_refill']
        bucket['tokens'] = min(
            self.capacity,
            bucket['tokens'] + elapsed * self.refill_rate
        )
        bucket['last_refill'] = now
        
        # Try to consume
        if bucket['tokens'] >= tokens:
            bucket['tokens'] -= tokens
            return True
        return False

rate_limiter = TokenBucket(capacity=10, refill_rate=1.0)
```

## Rate Limit Decorator

```python
def rate_limit(max_calls: int = 5, window: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            
            if not rate_limiter.consume(user_id):
                await update.message.reply_text(
                    "Too many requests. Please slow down."
                )
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=3, window=60)
async def expensive_command(update, context):
    # Process expensive operation
    pass
```

## Redis-based Rate Limiting

```python
class RedisRateLimiter:
    def __init__(self, redis_client, max_requests: int, window: int):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
    
    async def is_allowed(self, user_id: int) -> bool:
        key = f"rate_limit:{user_id}"
        
        # Increment counter
        count = await self.redis.incr(key)
        
        # Set expiry on first request
        if count == 1:
            await self.redis.expire(key, self.window)
        
        return count <= self.max_requests
```
