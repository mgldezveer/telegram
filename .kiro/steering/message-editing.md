# Message Editing

## Edit Text Message

```python
async def edit_message(update, context):
    """Edit a sent message."""
    message = await update.message.reply_text("Original text")
    
    await asyncio.sleep(2)
    
    await message.edit_text("Edited text")
```

## Edit with Markup

```python
async def edit_with_keyboard(update, context):
    """Edit message and keyboard."""
    keyboard = [
        [InlineKeyboardButton("New Button", callback_data="new")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "Updated message",
        reply_markup=reply_markup
    )
```

## Edit Media

```python
from telegram import InputMediaPhoto

async def edit_media(bot, chat_id: int, message_id: int):
    """Edit message media."""
    new_media = InputMediaPhoto(
        media=open('new_photo.jpg', 'rb'),
        caption="Updated caption"
    )
    
    await bot.edit_message_media(
        chat_id=chat_id,
        message_id=message_id,
        media=new_media
    )
```

## Edit Caption

```python
async def edit_caption(bot, chat_id: int, message_id: int):
    """Edit media caption."""
    await bot.edit_message_caption(
        chat_id=chat_id,
        message_id=message_id,
        caption="New caption"
    )
```

## Delete Message

```python
async def delete_message(update, context):
    """Delete a message."""
    await update.message.delete()
    
    # Delete specific message
    await context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=message_id
    )
```
