# Background Tasks

## Celery Integration

```python
from celery import Celery

celery_app = Celery('bot', broker='redis://localhost:6379/0')

@celery_app.task
def process_heavy_task(user_id: int, data: dict):
    """Process heavy computation in background."""
    result = expensive_computation(data)
    # Store result
    db.save_result(user_id, result)
    return result

async def heavy_command(update, context):
    user_id = update.effective_user.id
    data = {'input': context.args}
    
    # Queue task
    process_heavy_task.delay(user_id, data)
    
    await update.message.reply_text(
        "Task queued. You'll be notified when complete."
    )
```

## AsyncIO Tasks

```python
import asyncio

async def background_worker(bot, user_id: int):
    """Long-running background task."""
    await asyncio.sleep(10)  # Simulate work
    result = await perform_task()
    
    await bot.send_message(
        chat_id=user_id,
        text=f"Task complete: {result}"
    )

async def start_background_task(update, context):
    user_id = update.effective_user.id
    
    # Start task in background
    asyncio.create_task(background_worker(context.bot, user_id))
    
    await update.message.reply_text("Task started in background")
```

## Task Queue

```python
from asyncio import Queue

task_queue = Queue()

async def task_worker(bot):
    """Process tasks from queue."""
    while True:
        task = await task_queue.get()
        try:
            await process_task(bot, task)
        except Exception as e:
            logger.error(f"Task failed: {e}")
        finally:
            task_queue.task_done()

async def enqueue_task(update, context):
    task = {
        'user_id': update.effective_user.id,
        'data': context.args
    }
    await task_queue.put(task)
    await update.message.reply_text("Task queued")

# Start worker on bot startup
asyncio.create_task(task_worker(bot))
```
