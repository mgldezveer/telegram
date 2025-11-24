"""Configuration management for AI Content Bot."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Bot configuration."""
    token: str
    admin_ids: list[int]
    webhook_url: Optional[str] = None


@dataclass
class AIConfig:
    """AI provider configuration."""
    api_key: str
    provider: str = "groq"
    model: str = "qwen-2.5-72b-instruct"
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    pool_size: int = 10
    echo: bool = False


@dataclass
class RedisConfig:
    """Redis configuration."""
    url: str
    max_connections: int = 50


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    default_frequency: int = 3  # posts per day
    timezone: str = "UTC"


@dataclass
class Config:
    """Application configuration."""
    bot: BotConfig
    ai: AIConfig
    database: DatabaseConfig
    redis: RedisConfig
    scheduler: SchedulerConfig
    log_level: str
    debug: bool
    monitoring_port: int = 9090


def load_config() -> Config:
    """Load configuration from environment variables."""
    # Bot configuration
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
    
    bot_config = BotConfig(
        token=token,
        admin_ids=admin_ids,
        webhook_url=os.getenv("WEBHOOK_URL")
    )
    
    # AI configuration
    ai_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not ai_key:
        raise ValueError("GROQ_API_KEY or OPENAI_API_KEY environment variable is required")
    
    provider = "groq" if os.getenv("GROQ_API_KEY") else "openai"
    
    ai_config = AIConfig(
        api_key=ai_key,
        provider=provider,
        model=os.getenv("AI_MODEL", "qwen-2.5-72b-instruct" if provider == "groq" else "gpt-4"),
        temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("AI_MAX_TOKENS", "1000"))
    )
    
    # Database configuration
    db_config = DatabaseConfig(
        url=os.getenv("DATABASE_URL", "sqlite:///bot.db"),
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        echo=os.getenv("DB_ECHO", "false").lower() == "true"
    )
    
    # Redis configuration
    redis_config = RedisConfig(
        url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    )
    
    # Scheduler configuration
    scheduler_config = SchedulerConfig(
        default_frequency=int(os.getenv("DEFAULT_POSTING_FREQUENCY", "3")),
        timezone=os.getenv("TIMEZONE", "UTC")
    )
    
    return Config(
        bot=bot_config,
        ai=ai_config,
        database=db_config,
        redis=redis_config,
        scheduler=scheduler_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        monitoring_port=int(os.getenv("MONITORING_PORT", "9090"))
    )


# Global config instance
config = load_config()
