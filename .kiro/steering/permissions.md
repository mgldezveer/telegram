# Chat Permissions

## Set Default Permissions

```python
from telegram import ChatPermissions

async def set_default_permissions(bot, chat_id: int):
    """Set default permissions for all members."""
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False
    )
    
    await bot.set_chat_permissions(chat_id, permissions)
```

## Restrict User

```python
async def restrict_user(bot, chat_id: int, user_id: int):
    """Restrict user permissions."""
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False
    )
    
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions,
        until_date=None  # Permanent
    )
```

## Temporary Restriction

```python
from datetime import datetime, timedelta

async def temp_mute(bot, chat_id: int, user_id: int, minutes: int):
    """Temporarily mute user."""
    until = datetime.now() + timedelta(minutes=minutes)
    
    permissions = ChatPermissions(can_send_messages=False)
    
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions,
        until_date=until
    )
```

## Promote to Admin

```python
async def promote_user(bot, chat_id: int, user_id: int):
    """Promote user to administrator."""
    await bot.promote_chat_member(
        chat_id,
        user_id,
        can_change_info=True,
        can_delete_messages=True,
        can_invite_users=True,
        can_restrict_members=True,
        can_pin_messages=True,
        can_promote_members=False
    )
```

## Set Admin Title

```python
async def set_admin_title(bot, chat_id: int, user_id: int, title: str):
    """Set custom title for administrator."""
    await bot.set_chat_administrator_custom_title(
        chat_id,
        user_id,
        title
    )
```
