# Chat Information

## Get Chat Info

```python
async def get_chat_info(bot, chat_id: int):
    """Get detailed chat information."""
    chat = await bot.get_chat(chat_id)
    
    info = f"Title: {chat.title}\n"
    info += f"Type: {chat.type}\n"
    info += f"Username: @{chat.username}\n" if chat.username else ""
    info += f"Description: {chat.description}\n" if chat.description else ""
    info += f"Member count: {await bot.get_chat_member_count(chat_id)}\n"
    
    return info
```

## Get Chat Member

```python
async def get_member_info(bot, chat_id: int, user_id: int):
    """Get chat member information."""
    member = await bot.get_chat_member(chat_id, user_id)
    
    info = f"User: {member.user.first_name}\n"
    info += f"Status: {member.status}\n"
    
    if member.status == 'administrator':
        info += f"Can delete messages: {member.can_delete_messages}\n"
        info += f"Can restrict members: {member.can_restrict_members}\n"
    
    return info
```

## Get Chat Administrators

```python
async def get_admins(bot, chat_id: int):
    """Get list of chat administrators."""
    admins = await bot.get_chat_administrators(chat_id)
    
    admin_list = []
    for admin in admins:
        admin_list.append({
            'user_id': admin.user.id,
            'name': admin.user.first_name,
            'status': admin.status,
            'custom_title': admin.custom_title
        })
    
    return admin_list
```

## Set Chat Title/Description

```python
async def set_chat_title(bot, chat_id: int, title: str):
    """Set chat title."""
    await bot.set_chat_title(chat_id, title)

async def set_chat_description(bot, chat_id: int, description: str):
    """Set chat description."""
    await bot.set_chat_description(chat_id, description)
```

## Set Chat Photo

```python
async def set_chat_photo(bot, chat_id: int, photo_path: str):
    """Set chat photo."""
    with open(photo_path, 'rb') as photo:
        await bot.set_chat_photo(chat_id, photo)
```
