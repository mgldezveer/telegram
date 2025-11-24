# Analytics & Metrics

## Event Tracking

```python
from datetime import datetime

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

async def track_event(user_id: int, event_type: str, data: dict = None):
    event = Event(
        user_id=user_id,
        event_type=event_type,
        event_data=data
    )
    await db.add_event(event)
```

## Usage Tracking

```python
async def track_command(update, context):
    await track_event(
        user_id=update.effective_user.id,
        event_type='command',
        data={
            'command': update.message.text,
            'chat_type': update.effective_chat.type
        }
    )
```

## Analytics Queries

```python
async def get_daily_active_users(days: int = 7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    return await db.count_users_active_since(cutoff)

async def get_popular_commands(limit: int = 10):
    return await db.get_top_events('command', limit)

async def get_user_retention(days: int = 30):
    total = await db.count_users()
    active = await get_daily_active_users(days)
    return (active / total) * 100 if total > 0 else 0
```

## Metrics Export

```python
async def export_metrics():
    metrics = {
        'total_users': await db.count_users(),
        'active_today': await get_daily_active_users(1),
        'active_week': await get_daily_active_users(7),
        'retention_30d': await get_user_retention(30),
        'popular_commands': await get_popular_commands()
    }
    return metrics
```
