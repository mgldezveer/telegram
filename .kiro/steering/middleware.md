# Middleware

## What is Middleware

Middleware intercepts updates before they reach handlers, useful for:
- Logging
- Authentication
- Rate limiting
- Analytics

## Basic Middleware

```python
from telegram.ext import BaseMiddleware

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, update, context, next_handler):
        logger.info(f"Update from user {update.effective_user.id}")
        return await next_handler(update, context)
```

## Authentication Middleware

```python
class AuthMiddleware(BaseMiddleware):
    def __init__(self, allowed_users: list[int]):
        self.allowed_users = allowed_users
    
    async def __call__(self, update, context, next_handler):
        user_id = update.effective_user.id
        if user_id not in self.allowed_users:
            await update.message.reply_text("Access denied")
            return
        return await next_handler(update, context)
```

## Rate Limiting Middleware

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window)
        self.requests = defaultdict(list)
    
    async def __call__(self, update, context, next_handler):
        user_id = update.effective_user.id
        now = datetime.now()
        
        # Clean old requests
        self.requests[user_id] = [
            t for t in self.requests[user_id]
            if now - t < self.window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            await update.message.reply_text("Too many requests")
            return
        
        self.requests[user_id].append(now)
        return await next_handler(update, context)
```
