# Repository Pattern Implementation

## Overview

The AI Content Bot uses the Repository pattern to separate data access logic from business logic, providing a clean and maintainable architecture.

## Architecture

```
┌─────────────────────────────────────────┐
│         Service Layer                    │
│  (Business Logic)                        │
│                                          │
│  ChannelManager, ContentGenerator, etc. │
└──────────────────┬──────────────────────┘
                   │
                   │ Uses
                   ▼
┌─────────────────────────────────────────┐
│       Repository Layer                   │
│  (Data Access Abstraction)               │
│                                          │
│  ChannelRepository, PostRepository, etc. │
└──────────────────┬──────────────────────┘
                   │
                   │ Queries
                   ▼
┌─────────────────────────────────────────┐
│         Database Layer                   │
│  (SQLAlchemy ORM + PostgreSQL/SQLite)   │
└─────────────────────────────────────────┘
```

## Benefits

1. **Separation of Concerns**: Business logic is separated from data access
2. **Testability**: Easy to mock repositories for unit testing
3. **Maintainability**: Changes to data access don't affect business logic
4. **Consistency**: Standardized data access patterns across the application
5. **Flexibility**: Easy to switch database implementations

## Implementation Example

### Service Layer (ChannelManager)

```python
from src.models.base import async_session_maker
from src.repositories.channel_repository import ChannelRepository

class ChannelManager:
    async def get_all_channels(self) -> list[Channel]:
        """Get all registered channels."""
        async with async_session_maker() as session:
            repo = ChannelRepository(session)
            channels = await repo.get_all_active()
            return channels
```

### Repository Layer (ChannelRepository)

```python
from sqlalchemy import select
from src.models.channel import Channel

class ChannelRepository:
    def __init__(self, session):
        self.session = session
    
    async def get_all_active(self) -> list[Channel]:
        """Get all active channels."""
        result = await self.session.execute(
            select(Channel).where(Channel.active == True)
        )
        return result.scalars().all()
```

## Available Repositories

### ChannelRepository
- `get_all_active()` - Get all active channels
- `get_by_telegram_id(telegram_id)` - Find channel by Telegram ID
- `create(channel)` - Create new channel
- `update(channel)` - Update existing channel
- `delete(channel_id)` - Delete channel

### PostRepository
- `get_by_id(post_id)` - Get post by ID
- `get_by_channel(channel_id)` - Get all posts for a channel
- `get_scheduled()` - Get scheduled posts
- `create(post)` - Create new post
- `update(post)` - Update existing post

### MetricsRepository
- `get_by_channel(channel_id)` - Get metrics for a channel
- `get_by_post(post_id)` - Get metrics for a post
- `create(metrics)` - Create new metrics record
- `update(metrics)` - Update existing metrics

## Session Management

The application uses `async_session_maker` from `src/models/base.py` for database session management:

```python
from src.models.base import async_session_maker

async with async_session_maker() as session:
    # Session is automatically managed
    repo = SomeRepository(session)
    result = await repo.some_method()
    # Session is automatically committed/rolled back
```

## Best Practices

1. **Always use repositories**: Never access the database directly from services
2. **Keep repositories focused**: Each repository handles one model
3. **Use async sessions**: All database operations should be async
4. **Handle errors gracefully**: Repositories should let exceptions bubble up
5. **Keep business logic in services**: Repositories only handle data access

## Migration from Direct Access

**Before (Direct Database Access):**
```python
from src.database import get_session
from sqlalchemy import select

async with get_session() as session:
    result = await session.execute(
        select(Channel).where(Channel.active == True)
    )
    channels = result.scalars().all()
```

**After (Repository Pattern):**
```python
from src.models.base import async_session_maker
from src.repositories.channel_repository import ChannelRepository

async with async_session_maker() as session:
    repo = ChannelRepository(session)
    channels = await repo.get_all_active()
```

## Testing with Repositories

Repositories make testing easier by allowing mock implementations:

```python
from unittest.mock import AsyncMock

async def test_channel_manager():
    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_all_active.return_value = [mock_channel]
    
    # Test service with mock
    manager = ChannelManager()
    channels = await manager.get_all_channels()
    
    assert len(channels) == 1
```

## Future Enhancements

1. **Caching Layer**: Add Redis caching between service and repository
2. **Query Builder**: Add fluent query builder for complex queries
3. **Specification Pattern**: Add specifications for complex filtering
4. **Unit of Work**: Implement Unit of Work pattern for transactions

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Status**: Active
