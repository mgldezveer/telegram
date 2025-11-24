# Bot Menu Commands

## Setting Bot Menu

```python
from telegram import BotCommand

async def set_bot_commands(bot):
    """Set bot command menu."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help message"),
        BotCommand("settings", "Configure settings"),
        BotCommand("profile", "View your profile"),
        BotCommand("stats", "View statistics"),
        BotCommand("cancel", "Cancel current operation")
    ]
    await bot.set_my_commands(commands)
```

## Language-Specific Commands

```python
async def set_localized_commands(bot):
    """Set commands for different languages."""
    from telegram import BotCommandScopeDefault
    
    # English commands
    en_commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help")
    ]
    await bot.set_my_commands(
        en_commands,
        language_code="en"
    )
    
    # Russian commands
    ru_commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("help", "Показать помощь")
    ]
    await bot.set_my_commands(
        ru_commands,
        language_code="ru"
    )
```

## Scope-Specific Commands

```python
from telegram import BotCommandScopeChat, BotCommandScopeAllPrivateChats

async def set_admin_commands(bot, admin_chat_id: int):
    """Set admin-only commands."""
    admin_commands = [
        BotCommand("stats", "Bot statistics"),
        BotCommand("broadcast", "Send broadcast"),
        BotCommand("ban", "Ban user"),
        BotCommand("unban", "Unban user")
    ]
    
    await bot.set_my_commands(
        admin_commands,
        scope=BotCommandScopeChat(chat_id=admin_chat_id)
    )

async def set_private_commands(bot):
    """Commands for private chats only."""
    private_commands = [
        BotCommand("start", "Start bot"),
        BotCommand("profile", "Your profile")
    ]
    
    await bot.set_my_commands(
        private_commands,
        scope=BotCommandScopeAllPrivateChats()
    )
```
