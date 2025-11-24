# Groups & Channels

## Group Management

```python
async def new_member_handler(update, context):
    """Welcome new members."""
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"Welcome {member.first_name}!"
        )

async def left_member_handler(update, context):
    """Handle member leaving."""
    member = update.message.left_chat_member
    await update.message.reply_text(
        f"Goodbye {member.first_name}!"
    )

app.add_handler(MessageHandler(
    filters.StatusUpdate.NEW_CHAT_MEMBERS,
    new_member_handler
))
app.add_handler(MessageHandler(
    filters.StatusUpdate.LEFT_CHAT_MEMBER,
    left_member_handler
))
```

## Admin Commands

```python
async def kick_user(update, context):
    """Kick user from group."""
    if not context.args:
        await update.message.reply_text("Usage: /kick <user_id>")
        return
    
    user_id = int(context.args[0])
    chat_id = update.effective_chat.id
    
    try:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id)
        await update.message.reply_text("User kicked")
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")

async def mute_user(update, context):
    """Mute user in group."""
    user_id = int(context.args[0])
    chat_id = update.effective_chat.id
    
    from telegram import ChatPermissions
    
    await context.bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(can_send_messages=False)
    )
```

## Channel Posting

```python
async def post_to_channel(bot, channel_id: str, text: str):
    """Post message to channel."""
    await bot.send_message(chat_id=channel_id, text=text)

async def schedule_channel_post(context):
    """Scheduled channel post."""
    await post_to_channel(
        context.bot,
        CHANNEL_ID,
        "Daily update!"
    )
```
