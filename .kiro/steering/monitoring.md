# Monitoring & Observability

## Health Monitoring

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HealthStatus:
    status: str
    uptime: float
    memory_usage: float
    active_users: int
    timestamp: datetime

async def get_health_status() -> HealthStatus:
    """Get current health status."""
    import psutil
    
    process = psutil.Process()
    
    return HealthStatus(
        status='healthy',
        uptime=time.time() - start_time,
        memory_usage=process.memory_info().rss / 1024 / 1024,  # MB
        active_users=await db.count_active_users(),
        timestamp=datetime.utcnow()
    )
```

## Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
messages_total = Counter('bot_messages_total', 'Total messages processed')
command_duration = Histogram('bot_command_duration_seconds', 'Command processing time')
active_users = Gauge('bot_active_users', 'Number of active users')

# Usage
messages_total.inc()
with command_duration.time():
    await process_command()
active_users.set(await db.count_active_users())
```

## Error Tracking

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)

async def handle_error(update, context):
    """Global error handler."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Report to Sentry
    sentry_sdk.capture_exception(context.error)
```
