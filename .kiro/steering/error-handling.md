# Error Handling

## Exception Hierarchy

Create custom exceptions for different error types:

```python
class TelegramBotError(Exception):
    """Base exception for bot errors."""
    pass

class APIError(TelegramBotError):
    """Raised when Telegram API request fails."""
    pass

class ValidationError(TelegramBotError):
    """Raised when input validation fails."""
    pass

class DatabaseError(TelegramBotError):
    """Raised when database operation fails."""
    pass
```

## Error Handling Pattern

```python
import logging

logger = logging.getLogger(__name__)

async def handle_command(update, context):
    try:
        result = await process_command(update.message.text)
        await update.message.reply_text(result)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        await update.message.reply_text("Invalid input. Please try again.")
    except APIError as e:
        logger.error(f"API error: {e}")
        await update.message.reply_text("Service temporarily unavailable.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
```

## Logging

- Use Python's logging module
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include context in log messages
- Never log sensitive data (tokens, passwords)

## User-Facing Messages

- Be clear and helpful
- Don't expose internal errors
- Provide actionable guidance
- Use friendly tone
