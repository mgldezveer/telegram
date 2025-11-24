# Forward & Copy Messages

## Forward Message

```python
async def forward_message(bot, from_chat: int, to_chat: int, message_id: int):
    """Forward a message."""
    await bot.forward_message(
        chat_id=to_chat,
        from_chat_id=from_chat,
        message_id=message_id
    )
```

## Copy Message

```python
async def copy_message(bot, from_chat: int, to_chat: int, message_id: int):
    """Copy message without forward header."""
    await bot.copy_message(
        chat_id=to_chat,
        from_chat_id=from_chat,
        message_id=message_id
    )
```

## Copy with Modified Caption

```python
async def copy_with_caption(bot, from_chat: int, to_chat: int, message_id: int):
    """Copy message with new caption."""
    await bot.copy_message(
        chat_id=to_chat,
        from_chat_id=from_chat,
        message_id=message_id,
        caption="New caption for copied message"
    )
```

## Forward Multiple Messages

```python
async def forward_multiple(bot, from_chat: int, to_chat: int, message_ids: list[int]):
    """Forward multiple messages."""
    await bot.forward_messages(
        chat_id=to_chat,
        from_chat_id=from_chat,
        message_ids=message_ids
    )
```

## Copy Multiple Messages

```python
async def copy_multiple(bot, from_chat: int, to_chat: int, message_ids: list[int]):
    """Copy multiple messages."""
    await bot.copy_messages(
        chat_id=to_chat,
        from_chat_id=from_chat,
        message_ids=message_ids
    )
```
