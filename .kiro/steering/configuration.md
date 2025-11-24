# Configuration Management

## Configuration File

Create a centralized config module:

```python
# src/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BotConfig:
    """Bot configuration."""
    token: str
    admin_ids: list[int]
    webhook_url: str | None = None
    
@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    pool_size: int = 10
    echo: bool = False

@dataclass
class Config:
    """Application configuration."""
    bot: BotConfig
    database: DatabaseConfig
    log_level: str
    debug: bool

def load_config() -> Config:
    """Load configuration from environment."""
    return Config(
        bot=BotConfig(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            admin_ids=[int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id],
            webhook_url=os.getenv("WEBHOOK_URL")
        ),
        database=DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///bot.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )

# Global config instance
config = load_config()
```

## Environment Variables

Create `.env.example` template:

```
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
WEBHOOK_URL=

# Database
DATABASE_URL=sqlite:///bot.db
DB_POOL_SIZE=10
DB_ECHO=false

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

## Usage

```python
from src.config import config

# Access configuration
bot_token = config.bot.token
db_url = config.database.url
```

## Best Practices

- Validate required variables on startup
- Provide sensible defaults
- Document all configuration options
- Use type hints for configuration values
- Fail fast if critical config is missing
