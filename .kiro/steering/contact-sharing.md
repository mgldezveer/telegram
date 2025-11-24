# Contact Sharing

## Send Contact

```python
async def send_contact(update, context):
    """Send contact information."""
    await update.message.reply_contact(
        phone_number="+1234567890",
        first_name="John",
        last_name="Doe",
        vcard="BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nTEL:+1234567890\nEND:VCARD"
    )
```

## Request Contact

```python
from telegram import KeyboardButton, ReplyKeyboardMarkup

async def request_contact(update, context):
    """Request user's contact."""
    keyboard = [
        [KeyboardButton("Share Contact", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "Please share your contact:",
        reply_markup=reply_markup
    )
```

## Receive Contact

```python
async def contact_handler(update, context):
    """Handle received contact."""
    contact = update.message.contact
    
    logger.info(f"Received contact: {contact.first_name} {contact.last_name}")
    logger.info(f"Phone: {contact.phone_number}")
    logger.info(f"User ID: {contact.user_id}")
    
    # Save contact
    await db.save_contact(
        user_id=update.effective_user.id,
        phone=contact.phone_number,
        name=f"{contact.first_name} {contact.last_name}"
    )
    
    await update.message.reply_text("Contact saved!")

app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
```
