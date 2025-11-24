# Session Management

## User Sessions

```python
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self, timeout: int = 3600):
        self.sessions = {}
        self.timeout = timedelta(seconds=timeout)
    
    def create_session(self, user_id: int, data: dict = None):
        self.sessions[user_id] = {
            'data': data or {},
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
    
    def get_session(self, user_id: int):
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if datetime.now() - session['last_activity'] < self.timeout:
                session['last_activity'] = datetime.now()
                return session['data']
            else:
                del self.sessions[user_id]
        return None
    
    def update_session(self, user_id: int, data: dict):
        if user_id in self.sessions:
            self.sessions[user_id]['data'].update(data)
            self.sessions[user_id]['last_activity'] = datetime.now()
    
    def end_session(self, user_id: int):
        if user_id in self.sessions:
            del self.sessions[user_id]

session_manager = SessionManager()
```

## Session Middleware

```python
class SessionMiddleware(BaseMiddleware):
    async def __call__(self, update, context, next_handler):
        user_id = update.effective_user.id
        
        # Get or create session
        session = session_manager.get_session(user_id)
        if not session:
            session_manager.create_session(user_id)
        
        # Store session in context
        context.user_data['session'] = session
        
        return await next_handler(update, context)
```

## Session Data

```python
async def save_to_session(update, context, key: str, value):
    user_id = update.effective_user.id
    session_manager.update_session(user_id, {key: value})

async def get_from_session(update, context, key: str):
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)
    return session.get(key) if session else None
```
