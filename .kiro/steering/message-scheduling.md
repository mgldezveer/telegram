# Message Scheduling

## Schedule with Job Queue

```python
from datetime import datetime, timedelta

async def schedule_message(update, context):
    """Schedule a message for later."""
    # Schedule for 1 hour from now
    when = datetime.now() + timedelta(hours=1)
    
    context.job_queue.run_once(
        send_scheduled_message,
        when=when,
        data={
            'chat_id': update.effective_chat.id,
            'text': 'Scheduled message!'
        },
        name=f"scheduled_{update.effective_chat.id}"
    )
    
    await update.message.reply_text("Message scheduled!")

async def send_scheduled_message(context):
    """Send the scheduled message."""
    data = context.job.data
    await context.bot.send_message(
        chat_id=data['chat_id'],
        text=data['text']
    )
```

## Recurring Messages

```python
async def setup_daily_message(context, chat_id: int, hour: int, minute: int):
    """Setup daily recurring message."""
    import datetime
    
    context.job_queue.run_daily(
        send_daily_message,
        time=datetime.time(hour=hour, minute=minute),
        data={'chat_id': chat_id},
        name=f"daily_{chat_id}"
    )

async def send_daily_message(context):
    """Send daily message."""
    chat_id = context.job.data['chat_id']
    await context.bot.send_message(
        chat_id=chat_id,
        text="Good morning! ☀️"
    )
```

## Cancel Scheduled Message

```python
async def cancel_scheduled(update, context):
    """Cancel scheduled messages."""
    job_name = f"scheduled_{update.effective_chat.id}"
    
    jobs = context.job_queue.get_jobs_by_name(job_name)
    if jobs:
        for job in jobs:
            job.schedule_removal()
        await update.message.reply_text("Scheduled message cancelled")
    else:
        await update.message.reply_text("No scheduled messages")
```

## List Scheduled Messages

```python
async def list_scheduled(update, context):
    """List all scheduled messages."""
    jobs = context.job_queue.jobs()
    
    if not jobs:
        await update.message.reply_text("No scheduled messages")
        return
    
    message = "Scheduled messages:\n"
    for job in jobs:
        if job.name.startswith("scheduled_"):
            next_run = job.next_t
            message += f"- {job.name}: {next_run}\n"
    
    await update.message.reply_text(message)
```
