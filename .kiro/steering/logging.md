# Logging Standards

## Configuration

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configure logging for the application."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
```

## Usage

```python
import logging

logger = logging.getLogger(__name__)

# Different log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.exception("Exception with traceback")
```

## What to Log

- Application startup/shutdown
- User commands and interactions
- API requests and responses
- Errors and exceptions
- Performance metrics
- Security events

## What NOT to Log

- API tokens or passwords
- Personal user data (unless necessary and anonymized)
- Full message content (unless debugging)
- Credit card or payment information

## Log Levels

- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for potentially harmful situations
- ERROR: Error events that might still allow the application to continue
- CRITICAL: Critical events that may cause the application to abort
