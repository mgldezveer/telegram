# Message Filters

## Built-in Filters

```python
from telegram.ext import MessageHandler, filters

# Text messages
app.add_handler(MessageHandler(filters.TEXT, text_handler))

# Photos
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

# Documents
app.add_handler(MessageHandler(filters.Document.ALL, document_handler))

# Voice messages
app.add_handler(MessageHandler(filters.VOICE, voice_handler))

# Commands
app.add_handler(MessageHandler(filters.COMMAND, command_handler))

# Private chats only
app.add_handler(MessageHandler(filters.ChatType.PRIVATE, private_handler))

# Group chats only
app.add_handler(MessageHandler(filters.ChatType.GROUPS, group_handler))
```

## Custom Filters

```python
from telegram.ext import filters

class AdminFilter(filters.MessageFilter):
    def filter(self, message):
        return message.from_user.id in config.bot.admin_ids

admin_filter = AdminFilter()
app.add_handler(MessageHandler(admin_filter, admin_handler))
```

## Combining Filters

```python
# AND operator
app.add_handler(MessageHandler(
    filters.TEXT & filters.ChatType.PRIVATE,
    private_text_handler
))

# OR operator
app.add_handler(MessageHandler(
    filters.PHOTO | filters.VIDEO,
    media_handler
))

# NOT operator
app.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    non_command_text_handler
))
```

## Regex Filters

```python
# Match specific pattern
app.add_handler(MessageHandler(
    filters.Regex(r'^/start'),
    start_handler
))

# Match email
app.add_handler(MessageHandler(
    filters.Regex(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    email_handler
))
```
