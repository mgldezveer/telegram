# Database Guidelines

## Database Choice

Recommended options:
- SQLite - simple, file-based (development/small bots)
- PostgreSQL - production-ready, scalable
- Redis - caching and session storage

## ORM

Use SQLAlchemy for database operations:

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Async Database Access

Use async SQLAlchemy for non-blocking operations:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession)

async def get_user(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
```

## Migrations

Use Alembic for database migrations:

```bash
# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head
```

## Best Practices

- Use connection pooling
- Close sessions properly
- Use transactions for multiple operations
- Index frequently queried columns
- Validate data before database operations
