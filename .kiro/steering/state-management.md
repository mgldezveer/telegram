# State Management

## Conversation Handler

Manage multi-step conversations:

```python
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

# States
CHOOSING, TYPING_REPLY = range(2)

async def start(update, context):
    await update.message.reply_text("What's your name?")
    return CHOOSING

async def received_name(update, context):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("How old are you?")
    return TYPING_REPLY

async def received_age(update, context):
    context.user_data['age'] = update.message.text
    name = context.user_data['name']
    await update.message.reply_text(f"Nice to meet you, {name}!")
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT, received_name)],
        TYPING_REPLY: [MessageHandler(filters.TEXT, received_age)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
```

## User Data Storage

```python
# Store per-user data
context.user_data['key'] = 'value'

# Store per-chat data
context.chat_data['key'] = 'value'

# Store bot-wide data
context.bot_data['key'] = 'value'
```

## Persistent Storage

```python
from telegram.ext import PicklePersistence

persistence = PicklePersistence(filepath='bot_data.pkl')
app = Application.builder().token(TOKEN).persistence(persistence).build()
```
