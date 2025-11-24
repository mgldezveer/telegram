# Inline Mode

## Enable Inline Mode

Enable in BotFather:
- `/setinline` → Select bot → Set placeholder

## Inline Query Handler

```python
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
import uuid

async def inline_query(update, context):
    query = update.inline_query.query
    
    if not query:
        return
    
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Result 1",
            input_message_content=InputTextMessageContent(
                f"You searched for: {query}"
            ),
            description="Description of result 1"
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Result 2",
            input_message_content=InputTextMessageContent(
                f"Another result for: {query}"
            )
        )
    ]
    
    await update.inline_query.answer(results, cache_time=300)

app.add_handler(InlineQueryHandler(inline_query))
```

## Inline Result Types

```python
from telegram import (
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InlineQueryResultGif
)

# Photo result
InlineQueryResultPhoto(
    id=str(uuid.uuid4()),
    photo_url="https://example.com/photo.jpg",
    thumbnail_url="https://example.com/thumb.jpg"
)

# Video result
InlineQueryResultVideo(
    id=str(uuid.uuid4()),
    video_url="https://example.com/video.mp4",
    mime_type="video/mp4",
    thumbnail_url="https://example.com/thumb.jpg",
    title="Video title"
)
```

## Chosen Inline Result

```python
async def chosen_inline_result(update, context):
    result = update.chosen_inline_result
    logger.info(f"User chose: {result.result_id}")

from telegram.ext import ChosenInlineResultHandler
app.add_handler(ChosenInlineResultHandler(chosen_inline_result))
```
