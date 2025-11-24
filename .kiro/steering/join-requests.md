# Join Requests

## Handle Join Request

```python
async def join_request_handler(update, context):
    """Handle chat join requests."""
    request = update.chat_join_request
    
    user = request.from_user
    chat = request.chat
    
    logger.info(f"Join request from {user.first_name} to {chat.title}")
    
    # Auto-approve based on criteria
    if should_approve(user):
        await context.bot.approve_chat_join_request(
            chat_id=chat.id,
            user_id=user.id
        )
        await context.bot.send_message(
            chat_id=user.id,
            text=f"Welcome! Your request to join {chat.title} was approved."
        )
    else:
        await context.bot.decline_chat_join_request(
            chat_id=chat.id,
            user_id=user.id
        )

from telegram.ext import ChatJoinRequestHandler
app.add_handler(ChatJoinRequestHandler(join_request_handler))
```

## Approve Join Request

```python
async def approve_request(bot, chat_id: int, user_id: int):
    """Approve a join request."""
    await bot.approve_chat_join_request(chat_id, user_id)
```

## Decline Join Request

```python
async def decline_request(bot, chat_id: int, user_id: int):
    """Decline a join request."""
    await bot.decline_chat_join_request(chat_id, user_id)
```

## Approval Criteria

```python
def should_approve(user) -> bool:
    """Determine if user should be auto-approved."""
    # Check if user has profile photo
    if not user.photo:
        return False
    
    # Check if username exists
    if not user.username:
        return False
    
    # Check against blacklist
    if user.id in BLACKLIST:
        return False
    
    return True
```
