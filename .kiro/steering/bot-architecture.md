# Bot Architecture

## Project Structure

```
telegram-bot/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers/       # Command and message handlers
│   │   ├── middleware/     # Middleware components
│   │   └── utils/          # Utility functions
│   ├── services/           # Business logic
│   ├── models/             # Data models
│   └── config.py           # Configuration
├── tests/
├── docs/
├── .env.example
├── requirements.txt
└── main.py
```

## Handler Organization

Separate handlers by functionality:

```python
# handlers/commands.py
async def start_handler(update, context):
    pass

async def help_handler(update, context):
    pass

# handlers/messages.py
async def text_message_handler(update, context):
    pass

# handlers/callbacks.py
async def button_callback_handler(update, context):
    pass
```

## Application Setup

```python
# main.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from src.bot.handlers import commands, messages

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", commands.start_handler))
    app.add_handler(CommandHandler("help", commands.help_handler))
    app.add_handler(MessageHandler(filters.TEXT, messages.text_message_handler))
    
    # Start bot
    app.run_polling()

if __name__ == "__main__":
    main()
```

## Separation of Concerns

- Handlers: Handle Telegram updates
- Services: Business logic
- Models: Data structures
- Utils: Helper functions
