# Message Threading

## Reply to Message

```python
async def reply_to_message(update, context):
    """Reply to a specific message."""
    if update.message.reply_to_message:
        await update.message.reply_text(
            "This is a reply!",
            reply_to_message_id=update.message.reply_to_message.message_id
        )
```

## Quote Reply

```python
async def quote_reply(update, context):
    """Reply with quote."""
    if update.message.reply_to_message:
        original = update.message.reply_to_message.text
        await update.message.reply_text(
            f"> {original}\n\nYour reply here",
            reply_to_message_id=update.message.reply_to_message.message_id
        )
```

## Thread in Forum

```python
async def reply_in_thread(bot, chat_id: int, thread_id: int, text: str):
    """Reply in forum thread."""
    await bot.send_message(
        chat_id=chat_id,
        message_thread_id=thread_id,
        text=text
    )
```

## Get Reply Chain

```python
async def get_reply_chain(bot, chat_id: int, message_id: int):
    """Get chain of replies."""
    chain = []
    current_id = message_id
    
    while current_id:
        try:
            msg = await bot.forward_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=current_id
            )
            chain.append(msg)
            current_id = msg.reply_to_message.message_id if msg.reply_to_message else None
        except:
            break
    
    return chain
```
