# User Management

## User Model

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language_code = Column(String(10), default='en')
    is_banned = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
```

## User Registration

```python
async def register_user(update: Update):
    user = update.effective_user
    
    db_user = await db.get_user(user.id)
    if not db_user:
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )
        await db.add_user(db_user)
    else:
        db_user.last_active = datetime.utcnow()
        await db.update_user(db_user)
```

## User Middleware

```python
class UserMiddleware(BaseMiddleware):
    async def __call__(self, update, context, next_handler):
        if update.effective_user:
            await register_user(update)
            
            # Check if banned
            user = await db.get_user(update.effective_user.id)
            if user.is_banned:
                await update.message.reply_text("You are banned")
                return
        
        return await next_handler(update, context)
```

## User Preferences

```python
async def set_language(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /language <en|ru|es>")
        return
    
    lang = context.args[0]
    user = await db.get_user(update.effective_user.id)
    user.language_code = lang
    await db.update_user(user)
    
    await update.message.reply_text(f"Language set to {lang}")
```
