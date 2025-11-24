# Custom Emoji

## Get Custom Emoji Stickers

```python
async def get_custom_emoji(bot, emoji_ids: list[str]):
    """Get custom emoji sticker information."""
    stickers = await bot.get_custom_emoji_stickers(emoji_ids)
    
    for sticker in stickers:
        logger.info(f"Emoji: {sticker.emoji}")
        logger.info(f"Set: {sticker.set_name}")
    
    return stickers
```

## Send with Custom Emoji

```python
async def send_with_custom_emoji(update, context):
    """Send message with custom emoji."""
    # Custom emoji in text (requires Premium)
    text = "Hello with custom emoji! <tg-emoji emoji-id='5368324170671202286'>👍</tg-emoji>"
    
    await update.message.reply_text(
        text,
        parse_mode='HTML'
    )
```

## Extract Custom Emoji

```python
async def extract_custom_emoji(update, context):
    """Extract custom emoji from message."""
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'custom_emoji':
                emoji_id = entity.custom_emoji_id
                logger.info(f"Found custom emoji: {emoji_id}")
```
