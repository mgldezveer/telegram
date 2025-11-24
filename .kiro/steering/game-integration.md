# Game Integration

## Sending Game

```python
async def send_game(update, context):
    """Send a game."""
    await update.message.reply_game(
        game_short_name="your_game_name"
    )
```

## Game Callback Handler

```python
async def game_callback(update, context):
    """Handle game callback query."""
    query = update.callback_query
    
    # Generate game URL
    user_id = query.from_user.id
    game_url = f"https://your-game.com?user_id={user_id}"
    
    await query.answer(url=game_url)

from telegram.ext import CallbackQueryHandler
app.add_handler(CallbackQueryHandler(
    game_callback,
    pattern="^game:"
))
```

## Set Game Score

```python
async def set_score(bot, user_id: int, score: int, message_id: int, chat_id: int):
    """Set user's game score."""
    await bot.set_game_score(
        user_id=user_id,
        score=score,
        chat_id=chat_id,
        message_id=message_id,
        force=False  # Only update if higher
    )
```

## Get High Scores

```python
async def get_high_scores(bot, user_id: int, message_id: int, chat_id: int):
    """Get game high scores."""
    scores = await bot.get_game_high_scores(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id
    )
    
    leaderboard = "\n".join([
        f"{i+1}. {score.user.first_name}: {score.score}"
        for i, score in enumerate(scores)
    ])
    
    return leaderboard
```
