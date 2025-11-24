# Chat Actions

## Send Chat Action

```python
from telegram.constants import ChatAction

async def typing_action(update, context):
    """Show typing indicator."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    
    # Simulate processing
    await asyncio.sleep(2)
    
    await update.message.reply_text("Done!")
```

## Available Actions

```python
async def show_actions(update, context):
    """Demonstrate different chat actions."""
    chat_id = update.effective_chat.id
    
    # Typing
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(1)
    
    # Uploading photo
    await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
    await asyncio.sleep(1)
    
    # Recording video
    await context.bot.send_chat_action(chat_id, ChatAction.RECORD_VIDEO)
    await asyncio.sleep(1)
    
    # Uploading document
    await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_DOCUMENT)
```

## Action Decorator

```python
def with_typing(func):
    """Decorator to show typing action."""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        return await func(update, context, *args, **kwargs)
    return wrapper

@with_typing
async def slow_command(update, context):
    await asyncio.sleep(3)
    await update.message.reply_text("Complete!")
```
