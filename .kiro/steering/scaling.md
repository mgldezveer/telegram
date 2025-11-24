# Scaling Strategies

## Horizontal Scaling

### Multiple Bot Instances

```python
# Use Redis for shared state
import redis.asyncio as redis

redis_client = redis.Redis(host='localhost', port=6379)

# Store shared data
await redis_client.set(f"user:{user_id}", json.dumps(data))

# Retrieve shared data
data = await redis_client.get(f"user:{user_id}")
```

### Load Balancing

```nginx
upstream bot_servers {
    server bot1:8000;
    server bot2:8000;
    server bot3:8000;
}

server {
    location /webhook {
        proxy_pass http://bot_servers;
    }
}
```

## Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Use connection pooling
- Implement caching

## Database Scaling

### Read Replicas

```python
# Master for writes
master_engine = create_async_engine(MASTER_DB_URL)

# Replica for reads
replica_engine = create_async_engine(REPLICA_DB_URL)

async def read_data():
    async with replica_engine.connect() as conn:
        result = await conn.execute(query)
        return result

async def write_data():
    async with master_engine.connect() as conn:
        await conn.execute(insert_query)
```

### Sharding

```python
def get_shard(user_id: int) -> str:
    """Determine which shard to use."""
    shard_count = 4
    shard_id = user_id % shard_count
    return f"shard_{shard_id}"
```

## Message Queue

```python
from celery import Celery

celery_app = Celery('bot', broker='redis://localhost:6379/0')

@celery_app.task
def process_message(message_data):
    """Process message in background."""
    # Heavy processing
    pass

# Queue message
process_message.delay(message_data)
```
