# Reply Markup Patterns

## Force Reply

```python
from telegram import ForceReply

async def force_reply(update, context):
    """Force user to reply to this message."""
    await update.message.reply_text(
        "What's your name?",
        reply_markup=ForceReply(selective=True)
    )
```

## Remove Keyboard

```python
from telegram import ReplyKeyboardRemove

async def remove_keyboard(update, context):
    """Remove custom keyboard."""
    await update.message.reply_text(
        "Keyboard removed",
        reply_markup=ReplyKeyboardRemove()
    )
```

## Selective Reply Keyboard

```python
async def selective_keyboard(update, context):
    """Show keyboard only to mentioned users."""
    keyboard = [
        [KeyboardButton("Yes"), KeyboardButton("No")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        selective=True,  # Only show to mentioned users
        one_time_keyboard=True
    )
    
    await update.message.reply_text(
        "Do you agree?",
        reply_markup=reply_markup
    )
```

## Input Field Placeholder

```python
async def with_placeholder(update, context):
    """Keyboard with input field placeholder."""
    keyboard = [[KeyboardButton("Send")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        input_field_placeholder="Type your message here..."
    )
    
    await update.message.reply_text(
        "Send a message:",
        reply_markup=reply_markup
    )
```
