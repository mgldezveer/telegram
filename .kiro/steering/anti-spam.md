# Anti-Spam Measures

## Spam Detection

```python
import re
from collections import defaultdict
from datetime import datetime, timedelta

class SpamDetector:
    def __init__(self):
        self.message_history = defaultdict(list)
        self.spam_patterns = [
            r'(http|https)://[^\s]+',  # URLs
            r'@\w+',  # Mentions
            r'#\w+',  # Hashtags
        ]
    
    def is_spam(self, user_id: int, text: str) -> bool:
        now = datetime.now()
        
        # Check message frequency
        recent = [t for t in self.message_history[user_id] 
                 if now - t < timedelta(seconds=10)]
        
        if len(recent) > 5:
            return True
        
        # Check for spam patterns
        spam_count = sum(len(re.findall(pattern, text)) 
                        for pattern in self.spam_patterns)
        
        if spam_count > 3:
            return True
        
        self.message_history[user_id].append(now)
        return False

spam_detector = SpamDetector()
```

## Anti-Spam Middleware

```python
class AntiSpamMiddleware(BaseMiddleware):
    async def __call__(self, update, context, next_handler):
        if update.message and update.message.text:
            user_id = update.effective_user.id
            
            if spam_detector.is_spam(user_id, update.message.text):
                await update.message.delete()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Spam detected and removed."
                )
                return
        
        return await next_handler(update, context)
```

## Flood Control

```python
class FloodControl:
    def __init__(self, max_messages: int = 5, window: int = 10):
        self.max_messages = max_messages
        self.window = timedelta(seconds=window)
        self.user_messages = defaultdict(list)
    
    def check_flood(self, user_id: int) -> bool:
        now = datetime.now()
        cutoff = now - self.window
        
        # Remove old messages
        self.user_messages[user_id] = [
            t for t in self.user_messages[user_id] if t > cutoff
        ]
        
        if len(self.user_messages[user_id]) >= self.max_messages:
            return True
        
        self.user_messages[user_id].append(now)
        return False
```

## Ban Spammers

```python
async def ban_spammer(bot, chat_id: int, user_id: int):
    """Ban user for spamming."""
    await bot.ban_chat_member(chat_id, user_id)
    await db.mark_as_spammer(user_id)
```
