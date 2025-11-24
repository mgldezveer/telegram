# Security Guidelines

## Secrets Management

- Never commit API tokens, passwords, or keys
- Use environment variables for sensitive data
- Use `.env` file for local development (add to .gitignore)
- Use python-dotenv to load environment variables

## Environment Variables

Required variables:
- `TELEGRAM_BOT_TOKEN` - Bot API token from BotFather
- `DATABASE_URL` - Database connection string (if applicable)
- `API_KEY` - External API keys (if applicable)

## Best Practices

- Validate all user input
- Sanitize data before database operations
- Use parameterized queries to prevent SQL injection
- Implement rate limiting for bot commands
- Log security events
- Keep dependencies updated

## Example .env

```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=postgresql://user:pass@localhost/dbname
LOG_LEVEL=INFO
```

## Loading Secrets

```python
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")
```
