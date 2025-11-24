# Telegram Web Apps

## Web App Button

```python
from telegram import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup

async def show_web_app(update, context):
    """Show web app button."""
    keyboard = [
        [KeyboardButton(
            "Open Web App",
            web_app=WebAppInfo(url="https://your-webapp.com")
        )]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Click the button to open web app:",
        reply_markup=reply_markup
    )
```

## Inline Web App

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def inline_web_app(update, context):
    """Inline web app button."""
    keyboard = [
        [InlineKeyboardButton(
            "Open App",
            web_app=WebAppInfo(url="https://your-webapp.com")
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Open the web app:",
        reply_markup=reply_markup
    )
```

## Receiving Web App Data

```python
async def web_app_data_handler(update, context):
    """Handle data from web app."""
    data = update.message.web_app_data.data
    
    # Parse data (usually JSON)
    import json
    parsed_data = json.loads(data)
    
    await update.message.reply_text(
        f"Received data: {parsed_data}"
    )

app.add_handler(MessageHandler(
    filters.StatusUpdate.WEB_APP_DATA,
    web_app_data_handler
))
```

## Web App Example (HTML)

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <h1>Telegram Web App</h1>
    <button onclick="sendData()">Send Data</button>
    
    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();
        
        function sendData() {
            let data = {
                action: 'submit',
                value: 'test'
            };
            tg.sendData(JSON.stringify(data));
        }
    </script>
</body>
</html>
```
