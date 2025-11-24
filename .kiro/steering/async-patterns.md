# Async Programming Patterns

## Async/Await

Use async/await for all I/O operations:

```python
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler

async def start_command(update: Update, context):
    """Handle /start command."""
    await update.message.reply_text("Hello! I'm your bot.")

async def fetch_data(url: str) -> dict:
    """Fetch data from external API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## Concurrent Operations

Use `asyncio.gather()` for parallel operations:

```python
async def process_multiple_requests(requests):
    """Process multiple requests concurrently."""
    tasks = [process_request(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Timeouts

Always set timeouts for external operations:

```python
async def fetch_with_timeout(url: str, timeout: int = 10):
    """Fetch data with timeout."""
    try:
        async with asyncio.timeout(timeout):
            return await fetch_data(url)
    except asyncio.TimeoutError:
        logger.error(f"Request to {url} timed out")
        raise APIError("Request timed out")
```

## Best Practices

- Don't block the event loop
- Use async libraries (aiohttp, asyncpg, etc.)
- Handle cancellation properly
- Avoid mixing sync and async code
- Use `asyncio.create_task()` for background tasks
