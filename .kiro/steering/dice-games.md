# Dice & Games

## Send Dice

```python
async def send_dice(update, context):
    """Send animated dice."""
    dice = await update.message.reply_dice()
    
    # Value will be 1-6
    logger.info(f"Dice rolled: {dice.dice.value}")
```

## Different Dice Types

```python
from telegram.constants import DiceEmoji

async def send_different_dice(update, context):
    """Send different types of dice."""
    
    # Regular dice (1-6)
    await update.message.reply_dice(emoji=DiceEmoji.DICE)
    
    # Darts (1-6)
    await update.message.reply_dice(emoji=DiceEmoji.DARTS)
    
    # Basketball (1-5)
    await update.message.reply_dice(emoji=DiceEmoji.BASKETBALL)
    
    # Football (1-5)
    await update.message.reply_dice(emoji=DiceEmoji.FOOTBALL)
    
    # Slot machine (1-64)
    await update.message.reply_dice(emoji=DiceEmoji.SLOT_MACHINE)
    
    # Bowling (1-6)
    await update.message.reply_dice(emoji=DiceEmoji.BOWLING)
```

## Dice Handler

```python
async def dice_handler(update, context):
    """Handle dice messages."""
    dice = update.message.dice
    
    if dice.emoji == DiceEmoji.DICE:
        if dice.value == 6:
            await update.message.reply_text("🎉 You rolled a 6!")
        elif dice.value == 1:
            await update.message.reply_text("😢 You rolled a 1")
    
    elif dice.emoji == DiceEmoji.SLOT_MACHINE:
        if dice.value == 64:  # Jackpot
            await update.message.reply_text("🎰 JACKPOT!")

app.add_handler(MessageHandler(filters.Dice.ALL, dice_handler))
```
