# Admin Panel

## Admin Decorators

```python
from functools import wraps
from src.config import config

def admin_only(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in config.bot.admin_ids:
            await update.message.reply_text("Admin access required")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

@admin_only
async def admin_command(update, context):
    await update.message.reply_text("Admin command executed")
```

## Statistics Command

```python
@admin_only
async def stats_command(update, context):
    total_users = await db.count_users()
    active_today = await db.count_active_users(days=1)
    
    stats = f"""
📊 Bot Statistics
Total users: {total_users}
Active today: {active_today}
    """
    await update.message.reply_text(stats)
```

## Broadcast Command

```python
@admin_only
async def broadcast_command(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = " ".join(context.args)
    users = await db.get_all_users()
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(user.telegram_id, message)
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to {user.telegram_id}: {e}")
    
    await update.message.reply_text(
        f"Broadcast complete\nSent: {sent}\nFailed: {failed}"
    )
```

## Ban/Unban Users

```python
@admin_only
async def ban_user(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    
    user_id = int(context.args[0])
    await db.ban_user(user_id)
    await update.message.reply_text(f"User {user_id} banned")

@admin_only
async def unban_user(update, context):
    user_id = int(context.args[0])
    await db.unban_user(user_id)
    await update.message.reply_text(f"User {user_id} unbanned")
```
