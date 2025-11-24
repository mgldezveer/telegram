# Notifications & Scheduling

## Scheduled Messages

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def send_daily_reminder(bot, user_id: int):
    await bot.send_message(
        chat_id=user_id,
        text="Daily reminder!"
    )

# Schedule daily at 9 AM
scheduler.add_job(
    send_daily_reminder,
    'cron',
    hour=9,
    minute=0,
    args=[bot, user_id]
)

scheduler.start()
```

## Job Queue

```python
from telegram.ext import JobQueue

async def callback_timer(context):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="Timer finished!"
    )

async def set_timer(update, context):
    chat_id = update.effective_chat.id
    
    # Run once after 60 seconds
    context.job_queue.run_once(
        callback_timer,
        60,
        chat_id=chat_id,
        name=f"timer_{chat_id}"
    )
    
    await update.message.reply_text("Timer set for 60 seconds")
```

## Recurring Jobs

```python
async def daily_job(context):
    users = await db.get_subscribed_users()
    for user in users:
        await context.bot.send_message(
            chat_id=user.telegram_id,
            text="Daily update!"
        )

# Run daily at specific time
context.job_queue.run_daily(
    daily_job,
    time=datetime.time(hour=9, minute=0)
)
```

## Cancel Jobs

```python
async def cancel_timer(update, context):
    chat_id = update.effective_chat.id
    job_name = f"timer_{chat_id}"
    
    jobs = context.job_queue.get_jobs_by_name(job_name)
    if jobs:
        for job in jobs:
            job.schedule_removal()
        await update.message.reply_text("Timer cancelled")
    else:
        await update.message.reply_text("No active timer")
```
