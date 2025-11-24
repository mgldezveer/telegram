# Polls & Quizzes

## Creating Polls

```python
async def create_poll(update, context):
    """Create a poll."""
    await update.message.reply_poll(
        question="What's your favorite color?",
        options=["Red", "Blue", "Green", "Yellow"],
        is_anonymous=True,
        allows_multiple_answers=False
    )
```

## Creating Quizzes

```python
async def create_quiz(update, context):
    """Create a quiz with correct answer."""
    await update.message.reply_poll(
        question="What is 2 + 2?",
        options=["3", "4", "5", "6"],
        type="quiz",
        correct_option_id=1,  # Index of correct answer (4)
        explanation="2 + 2 equals 4",
        is_anonymous=False
    )
```

## Poll Answer Handler

```python
async def poll_answer_handler(update, context):
    """Handle poll answers."""
    answer = update.poll_answer
    user_id = answer.user.id
    poll_id = answer.poll_id
    option_ids = answer.option_ids
    
    logger.info(f"User {user_id} voted {option_ids} in poll {poll_id}")
    
    # Store answer in database
    await db.save_poll_answer(user_id, poll_id, option_ids)

from telegram.ext import PollAnswerHandler
app.add_handler(PollAnswerHandler(poll_answer_handler))
```

## Stop Poll

```python
async def stop_poll(update, context):
    """Stop an active poll."""
    # Reply to the poll message with /stop
    if update.message.reply_to_message:
        poll_message = update.message.reply_to_message
        result = await context.bot.stop_poll(
            chat_id=poll_message.chat_id,
            message_id=poll_message.message_id
        )
        await update.message.reply_text(
            f"Poll stopped. Final results: {result.total_voter_count} votes"
        )
```
