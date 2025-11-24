# Graceful Shutdown

## Shutdown Handler

```python
import signal
import asyncio

class BotApplication:
    def __init__(self):
        self.is_running = True
        self.cleanup_tasks = []
    
    def register_cleanup(self, task):
        """Register cleanup task."""
        self.cleanup_tasks.append(task)
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down gracefully...")
        self.is_running = False
        
        # Stop accepting new updates
        await self.bot.stop()
        
        # Complete pending tasks
        pending = asyncio.all_tasks()
        await asyncio.gather(*pending, return_exceptions=True)
        
        # Run cleanup tasks
        for task in self.cleanup_tasks:
            try:
                await task()
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
        
        # Close connections
        await self.db.close()
        await self.redis.close()
        
        logger.info("Shutdown complete")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: asyncio.create_task(self.shutdown()))

# Usage
app = BotApplication()
app.setup_signal_handlers()
```

## Cleanup Tasks

```python
async def cleanup_temp_files():
    """Clean up temporary files."""
    import shutil
    shutil.rmtree('temp', ignore_errors=True)

async def save_state():
    """Save application state."""
    state = {
        'active_sessions': len(session_manager.sessions),
        'timestamp': datetime.utcnow().isoformat()
    }
    with open('state.json', 'w') as f:
        json.dump(state, f)

app.register_cleanup(cleanup_temp_files)
app.register_cleanup(save_state)
```
