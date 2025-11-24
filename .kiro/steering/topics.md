# Forum Topics

## Create Topic

```python
async def create_topic(bot, chat_id: int, name: str):
    """Create a forum topic."""
    topic = await bot.create_forum_topic(
        chat_id=chat_id,
        name=name,
        icon_color=0x6FB9F0,  # Blue
        icon_custom_emoji_id="5312536423851630001"  # Optional
    )
    return topic.message_thread_id
```

## Edit Topic

```python
async def edit_topic(bot, chat_id: int, thread_id: int, new_name: str):
    """Edit forum topic."""
    await bot.edit_forum_topic(
        chat_id=chat_id,
        message_thread_id=thread_id,
        name=new_name
    )
```

## Close/Reopen Topic

```python
async def close_topic(bot, chat_id: int, thread_id: int):
    """Close a forum topic."""
    await bot.close_forum_topic(
        chat_id=chat_id,
        message_thread_id=thread_id
    )

async def reopen_topic(bot, chat_id: int, thread_id: int):
    """Reopen a forum topic."""
    await bot.reopen_forum_topic(
        chat_id=chat_id,
        message_thread_id=thread_id
    )
```

## Delete Topic

```python
async def delete_topic(bot, chat_id: int, thread_id: int):
    """Delete a forum topic."""
    await bot.delete_forum_topic(
        chat_id=chat_id,
        message_thread_id=thread_id
    )
```

## Send to Topic

```python
async def send_to_topic(bot, chat_id: int, thread_id: int, text: str):
    """Send message to specific topic."""
    await bot.send_message(
        chat_id=chat_id,
        message_thread_id=thread_id,
        text=text
    )
```
