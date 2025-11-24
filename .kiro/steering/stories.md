# Stories

## Post Story

```python
async def post_story(bot, chat_id: int):
    """Post a story."""
    with open('story_media.jpg', 'rb') as media:
        story = await bot.send_story(
            chat_id=chat_id,
            media=media
        )
    return story
```

## Story with Privacy Settings

```python
from telegram import StoryPrivacySettings

async def post_private_story(bot, chat_id: int, allowed_users: list[int]):
    """Post story visible to specific users."""
    privacy = StoryPrivacySettings(
        allowed_user_ids=allowed_users
    )
    
    with open('story.jpg', 'rb') as media:
        await bot.send_story(
            chat_id=chat_id,
            media=media,
            privacy_settings=privacy
        )
```

## Delete Story

```python
async def delete_story(bot, chat_id: int, story_id: int):
    """Delete a story."""
    await bot.delete_story(
        chat_id=chat_id,
        story_id=story_id
    )
```
