# Invite Links

## Create Invite Link

```python
async def create_invite_link(bot, chat_id: int):
    """Create a new invite link."""
    link = await bot.create_chat_invite_link(chat_id)
    return link.invite_link
```

## Create Link with Limits

```python
from datetime import datetime, timedelta

async def create_limited_link(bot, chat_id: int):
    """Create invite link with limitations."""
    expire_date = datetime.now() + timedelta(days=7)
    
    link = await bot.create_chat_invite_link(
        chat_id,
        name="Limited Link",
        expire_date=expire_date,
        member_limit=100,
        creates_join_request=False
    )
    
    return link.invite_link
```

## Create Join Request Link

```python
async def create_approval_link(bot, chat_id: int):
    """Create link that requires approval."""
    link = await bot.create_chat_invite_link(
        chat_id,
        name="Approval Required",
        creates_join_request=True
    )
    
    return link.invite_link
```

## Edit Invite Link

```python
async def edit_invite_link(bot, chat_id: int, invite_link: str):
    """Edit existing invite link."""
    edited = await bot.edit_chat_invite_link(
        chat_id,
        invite_link,
        name="Updated Link",
        member_limit=50
    )
    
    return edited
```

## Revoke Invite Link

```python
async def revoke_link(bot, chat_id: int, invite_link: str):
    """Revoke an invite link."""
    await bot.revoke_chat_invite_link(chat_id, invite_link)
```

## Get Primary Link

```python
async def export_link(bot, chat_id: int):
    """Get primary invite link."""
    link = await bot.export_chat_invite_link(chat_id)
    return link
```
