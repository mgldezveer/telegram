# Troubleshooting Guide

## Common Issues

### Bot Not Responding

1. Check bot token is correct
2. Verify bot is running
3. Check network connectivity
4. Review logs for errors
5. Ensure webhook is set correctly (if using)

### Database Connection Errors

```python
# Test database connection
async def test_db_connection():
    try:
        await db.ping()
        logger.info("Database connection OK")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
```

### Memory Leaks

```python
# Monitor memory usage
import psutil
import gc

def check_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"Memory usage: {memory_mb:.2f} MB")
    
    if memory_mb > 500:  # Alert if over 500MB
        logger.warning("High memory usage detected")
        gc.collect()  # Force garbage collection
```

### Rate Limiting Issues

- Check Telegram API limits (30 messages/second)
- Implement proper rate limiting
- Use message queues for bulk operations

### Webhook Problems

```python
# Check webhook status
async def check_webhook(bot):
    info = await bot.get_webhook_info()
    logger.info(f"Webhook URL: {info.url}")
    logger.info(f"Pending updates: {info.pending_update_count}")
    logger.info(f"Last error: {info.last_error_message}")
```

## Debug Mode

```python
# Enable debug logging
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Performance Profiling

```python
import cProfile
import pstats

def profile_function(func):
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result
```
