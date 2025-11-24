# Deep Linking

## Start Parameter

```python
async def start_command(update, context):
    """Handle /start with parameter."""
    if context.args:
        param = context.args[0]
        
        if param.startswith('ref_'):
            referrer_id = param[4:]
            await handle_referral(update.effective_user.id, referrer_id)
        elif param.startswith('product_'):
            product_id = param[8:]
            await show_product(update, product_id)
    else:
        await update.message.reply_text("Welcome!")
```

## Generate Deep Link

```python
def generate_deep_link(bot_username: str, parameter: str) -> str:
    """Generate deep link."""
    return f"https://t.me/{bot_username}?start={parameter}"

# Usage
referral_link = generate_deep_link("mybot", f"ref_{user_id}")
product_link = generate_deep_link("mybot", f"product_{product_id}")
```

## Deep Link for Groups

```python
def generate_group_link(bot_username: str, parameter: str) -> str:
    """Generate link to add bot to group."""
    return f"https://t.me/{bot_username}?startgroup={parameter}"
```

## Deep Link for Channels

```python
def generate_channel_link(bot_username: str, parameter: str) -> str:
    """Generate link to add bot to channel."""
    return f"https://t.me/{bot_username}?startchannel={parameter}"
```

## Track Deep Links

```python
async def track_deep_link(user_id: int, parameter: str):
    """Track deep link usage."""
    await db.save_deep_link_click(
        user_id=user_id,
        parameter=parameter,
        timestamp=datetime.utcnow()
    )
```
