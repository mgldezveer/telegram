# Stickers

## Sending Stickers

```python
async def send_sticker(update, context):
    """Send a sticker."""
    # By file_id
    await update.message.reply_sticker(
        sticker="CAACAgIAAxkBAAEBAAFiQ..."
    )
    
    # From file
    with open('sticker.webp', 'rb') as sticker:
        await update.message.reply_sticker(sticker)
```

## Receiving Stickers

```python
async def sticker_handler(update, context):
    """Handle received stickers."""
    sticker = update.message.sticker
    
    logger.info(f"Received sticker: {sticker.file_id}")
    logger.info(f"Set name: {sticker.set_name}")
    logger.info(f"Emoji: {sticker.emoji}")
    
    # Download sticker
    file = await context.bot.get_file(sticker.file_id)
    await file.download_to_drive(f'sticker_{sticker.file_id}.webp')

app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_handler))
```

## Get Sticker Set

```python
async def get_sticker_set(bot, set_name: str):
    """Get sticker set information."""
    sticker_set = await bot.get_sticker_set(set_name)
    
    info = f"Sticker Set: {sticker_set.title}\n"
    info += f"Stickers: {len(sticker_set.stickers)}\n"
    
    return info
```

## Create Sticker Set

```python
async def create_sticker_set(bot, user_id: int):
    """Create a new sticker set."""
    await bot.create_new_sticker_set(
        user_id=user_id,
        name=f"my_stickers_by_{bot.username}",
        title="My Stickers",
        stickers=[{
            'sticker': open('sticker1.webp', 'rb'),
            'emoji_list': ['😀']
        }]
    )
```

## Add Sticker to Set

```python
async def add_sticker(bot, user_id: int, set_name: str):
    """Add sticker to existing set."""
    await bot.add_sticker_to_set(
        user_id=user_id,
        name=set_name,
        sticker={
            'sticker': open('new_sticker.webp', 'rb'),
            'emoji_list': ['🎉']
        }
    )
```
