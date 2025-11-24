# Keyboard Interfaces

## Reply Keyboards

Standard keyboard that replaces user's keyboard:

```python
from telegram import ReplyKeyboardMarkup, KeyboardButton

async def show_main_menu(update: Update, context):
    """Display main menu with reply keyboard."""
    keyboard = [
        [KeyboardButton("📊 Statistics"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("ℹ️ Help"), KeyboardButton("❌ Cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        "Choose an option:",
        reply_markup=reply_markup
    )
```

## Inline Keyboards

Buttons attached to messages:

```python
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def show_inline_menu(update: Update, context):
    """Display inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="opt_1"),
            InlineKeyboardButton("Option 2", callback_data="opt_2")
        ],
        [InlineKeyboardButton("Back", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select an option:",
        reply_markup=reply_markup
    )
```

## Callback Query Handler

Handle inline button clicks:

```python
from telegram.ext import CallbackQueryHandler

async def button_callback(update: Update, context):
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    if query.data == "opt_1":
        await query.edit_message_text("You selected Option 1")
    elif query.data == "opt_2":
        await query.edit_message_text("You selected Option 2")
    elif query.data == "back":
        await show_main_menu(query, context)

# Register handler
app.add_handler(CallbackQueryHandler(button_callback))
```

## Remove Keyboard

```python
from telegram import ReplyKeyboardRemove

async def remove_keyboard(update: Update, context):
    """Remove reply keyboard."""
    await update.message.reply_text(
        "Keyboard removed",
        reply_markup=ReplyKeyboardRemove()
    )
```

## Request Contact/Location

```python
keyboard = [
    [KeyboardButton("📱 Share Contact", request_contact=True)],
    [KeyboardButton("📍 Share Location", request_location=True)]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
```

## URL Buttons

```python
keyboard = [
    [InlineKeyboardButton("Visit Website", url="https://example.com")],
    [InlineKeyboardButton("Open Bot", url="https://t.me/your_bot")]
]
```

## Best Practices

- Use emojis for better UX
- Keep button text short and clear
- Limit rows to 2-3 buttons for readability
- Always handle callback queries with `query.answer()`
- Use `resize_keyboard=True` for reply keyboards
- Provide a way to go back or cancel
