# Input Validation

## Pydantic Models

```python
from pydantic import BaseModel, validator, Field
from typing import Optional

class UserInput(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    age: int = Field(..., ge=0, le=150)
    email: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email')
        return v
```

## Command Argument Validation

```python
from typing import List

def validate_args(min_args: int = 0, max_args: int = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            arg_count = len(context.args)
            
            if arg_count < min_args:
                await update.message.reply_text(
                    f"Not enough arguments. Expected at least {min_args}"
                )
                return
            
            if max_args and arg_count > max_args:
                await update.message.reply_text(
                    f"Too many arguments. Expected at most {max_args}"
                )
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

@validate_args(min_args=1, max_args=3)
async def search_command(update, context):
    query = " ".join(context.args)
    # Process search
```

## Sanitization

```python
import re
from html import escape

def sanitize_input(text: str) -> str:
    """Remove potentially dangerous characters."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Escape special characters
    text = escape(text)
    return text.strip()

def validate_user_id(user_id: str) -> Optional[int]:
    """Validate and convert user ID."""
    try:
        uid = int(user_id)
        if uid > 0:
            return uid
    except ValueError:
        pass
    return None
```
