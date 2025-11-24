# Environment Variables

## Required Variables

```bash
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
BOT_USERNAME=your_bot_username

# Admin Configuration
ADMIN_IDS=123456789,987654321

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/botdb
DB_POOL_SIZE=10
DB_ECHO=false

# Redis
REDIS_URL=redis://localhost:6379/0

# Webhook (if using)
WEBHOOK_URL=https://yourdomain.com
WEBHOOK_PORT=8443
WEBHOOK_SECRET=your_webhook_secret

# External APIs
WEATHER_API_KEY=your_weather_api_key
TRANSLATION_API_KEY=your_translation_api_key

# AWS (if using)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log

# Features
DEBUG=false
ENABLE_ANALYTICS=true
ENABLE_CACHING=true

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Session
SESSION_TIMEOUT=3600
```

## .env.example Template

```bash
# Copy this file to .env and fill in your values

# Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=

# Admin User IDs (comma-separated)
ADMIN_IDS=

# Database URL
DATABASE_URL=sqlite:///bot.db

# Redis URL (optional)
REDIS_URL=redis://localhost:6379/0

# Webhook URL (optional, for production)
WEBHOOK_URL=

# Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Debug Mode
DEBUG=false
```

## Loading Environment Variables

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Required variables
REQUIRED_VARS = ['TELEGRAM_BOT_TOKEN']

for var in REQUIRED_VARS:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")
```
