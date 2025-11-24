# Business Connection

## Handle Business Connection

```python
async def business_connection_handler(update, context):
    """Handle business connection updates."""
    connection = update.business_connection
    
    if connection.is_enabled:
        logger.info(f"Business connected: {connection.user_chat_id}")
        # Store connection
        await db.save_business_connection(
            user_id=connection.user.id,
            connection_id=connection.id
        )
    else:
        logger.info(f"Business disconnected: {connection.user_chat_id}")
        await db.remove_business_connection(connection.id)

from telegram.ext import BusinessConnectionHandler
app.add_handler(BusinessConnectionHandler(business_connection_handler))
```

## Business Messages

```python
async def business_message_handler(update, context):
    """Handle messages from business chats."""
    message = update.business_message
    
    # Process business message
    response = await process_business_query(message.text)
    
    # Reply to business chat
    await context.bot.send_message(
        business_connection_id=message.business_connection_id,
        chat_id=message.chat.id,
        text=response
    )

from telegram.ext import BusinessMessagesHandler
app.add_handler(BusinessMessagesHandler(business_message_handler))
```
