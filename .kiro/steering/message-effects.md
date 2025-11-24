# Message Effects

## Send with Effect

```python
async def send_with_effect(update, context):
    """Send message with visual effect."""
    await update.message.reply_text(
        "🎉 Celebration!",
        message_effect_id="5104841245755180586"  # Celebration effect
    )
```

## Available Effects

```python
EFFECTS = {
    'fire': '5104841245755180586',
    'heart': '5107584321108051014',
    'thumbs_up': '5107584321108051015',
    'party': '5104841245755180587'
}

async def send_fire_effect(update, context):
    await update.message.reply_text(
        "🔥 On fire!",
        message_effect_id=EFFECTS['fire']
    )
```
