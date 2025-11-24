# Message Pinning

## Pin Message

```python
async def pin_message(update, context):
    """Pin a message in chat."""
    if update.message.reply_to_message:
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.message_id,
            disable_notification=False
        )
        await update.message.reply_text("Message pinned!")
```

## Unpin Message

```python
async def unpin_message(update, context):
    """Unpin a specific message."""
    if update.message.reply_to_message:
        await context.bot.unpin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.message_id
        )
```

## Unpin All Messages

```python
async def unpin_all(update, context):
    """Unpin all messages in chat."""
    await context.bot.unpin_all_chat_messages(
        chat_id=update.effective_chat.id
    )
    await update.message.reply_text("All messages unpinned")
```

## Get Pinned Messages

```python
async def get_pinned(bot, chat_id: int):
    """Get all pinned messages."""
    chat = await bot.get_chat(chat_id)
    
    if chat.pinned_message:
        return chat.pinned_message
    return None
```
