# Bot Information

## Get Bot Info

```python
async def get_bot_info(bot):
    """Get bot information."""
    me = await bot.get_me()
    
    info = f"Bot username: @{me.username}\n"
    info += f"Bot ID: {me.id}\n"
    info += f"First name: {me.first_name}\n"
    info += f"Can join groups: {me.can_join_groups}\n"
    info += f"Can read messages: {me.can_read_all_group_messages}\n"
    info += f"Supports inline: {me.supports_inline_queries}\n"
    
    return info
```

## Set Bot Name

```python
async def set_bot_name(bot, name: str, language_code: str = None):
    """Set bot name."""
    await bot.set_my_name(name, language_code=language_code)
```

## Set Bot Description

```python
async def set_bot_description(bot, description: str, language_code: str = None):
    """Set bot description."""
    await bot.set_my_description(description, language_code=language_code)
```

## Set Bot Short Description

```python
async def set_short_description(bot, short_description: str, language_code: str = None):
    """Set bot short description."""
    await bot.set_my_short_description(
        short_description,
        language_code=language_code
    )
```

## Get Bot Commands

```python
async def get_commands(bot):
    """Get bot commands."""
    commands = await bot.get_my_commands()
    
    for cmd in commands:
        logger.info(f"/{cmd.command} - {cmd.description}")
    
    return commands
```

## Delete Bot Commands

```python
async def delete_commands(bot):
    """Delete all bot commands."""
    await bot.delete_my_commands()
```
