# Chat Boosts

## Boost Handler

```python
async def boost_added_handler(update, context):
    """Handle when user boosts chat."""
    boost = update.chat_boost
    
    await update.effective_chat.send_message(
        f"Thanks {boost.boost.source.user.first_name} for boosting! 🚀"
    )
    
    # Track boost
    await db.track_boost(
        user_id=boost.boost.source.user.id,
        chat_id=update.effective_chat.id
    )

from telegram.ext import ChatBoostHandler
app.add_handler(ChatBoostHandler(boost_added_handler))
```

## Get Chat Boosts

```python
async def get_boosts(bot, chat_id: int):
    """Get chat boost information."""
    boosts = await bot.get_user_chat_boosts(chat_id)
    
    info = f"Total boosts: {len(boosts.boosts)}\n"
    for boost in boosts.boosts:
        info += f"- {boost.source.user.first_name}\n"
    
    return info
```
