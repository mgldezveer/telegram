# Feedback System

## Feedback Model

```python
class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 stars
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='pending')
```

## Feedback Command

```python
async def feedback_command(update, context):
    """Start feedback conversation."""
    await update.message.reply_text(
        "Please send your feedback:",
        reply_markup=ForceReply()
    )
    return WAITING_FEEDBACK

async def receive_feedback(update, context):
    """Receive and save feedback."""
    feedback = Feedback(
        user_id=update.effective_user.id,
        message=update.message.text
    )
    await db.add_feedback(feedback)
    
    await update.message.reply_text(
        "Thank you for your feedback! 🙏"
    )
    
    # Notify admins
    for admin_id in config.bot.admin_ids:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"New feedback from {update.effective_user.first_name}:\n\n{update.message.text}"
        )
    
    return ConversationHandler.END
```

## Rating System

```python
async def request_rating(update, context):
    """Request rating from user."""
    keyboard = [
        [InlineKeyboardButton(f"{'⭐' * i}", callback_data=f"rate_{i}")]
        for i in range(1, 6)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "How would you rate your experience?",
        reply_markup=reply_markup
    )

async def rating_callback(update, context):
    """Handle rating selection."""
    query = update.callback_query
    rating = int(query.data.split('_')[1])
    
    await db.save_rating(query.from_user.id, rating)
    
    await query.answer()
    await query.edit_message_text(
        f"Thank you for rating us {'⭐' * rating}!"
    )
```
