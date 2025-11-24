# Bot Commands

## Standard Commands

Every bot should implement these basic commands:

- `/start` - Initialize bot, show welcome message
- `/help` - Display available commands and usage
- `/settings` - User settings and preferences
- `/cancel` - Cancel current operation

## Command Structure

```python
from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hello {user.first_name}! Welcome to the bot."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/settings - Configure bot settings
/cancel - Cancel current operation
    """
    await update.message.reply_text(help_text)
```

## Command with Arguments

```python
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search <query> command."""
    if not context.args:
        await update.message.reply_text("Usage: /search <query>")
        return
    
    query = " ".join(context.args)
    results = await perform_search(query)
    await update.message.reply_text(f"Results for '{query}':\n{results}")
```

## Admin Commands

```python
from src.config import config

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in config.bot.admin_ids

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("This command is only for administrators.")
        return
    
    # Admin logic here
    await update.message.reply_text("Admin command executed.")
```

## Command Registration

```python
from telegram.ext import Application, CommandHandler

def register_commands(app: Application):
    """Register all bot commands."""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("admin", admin_command))
```

## BotFather Command List

Set commands in BotFather for autocomplete:

```
start - Start the bot
help - Show help message
settings - Configure settings
search - Search for content
cancel - Cancel operation
```
