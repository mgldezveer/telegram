"""Improved logging configuration with structured logging and security."""

import logging
import sys
import json
import hashlib
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
import os


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs."""
    
    SENSITIVE_KEYS = {
        'token', 'password', 'api_key', 'secret', 'authorization',
        'credit_card', 'ssn', 'phone', 'email'
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in log record."""
        # Mask in message
        if hasattr(record, 'msg'):
            record.msg = self._mask_sensitive(str(record.msg))
        
        # Mask in extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                    record.__dict__[key] = self._mask_value(value)
        
        return True
    
    def _mask_sensitive(self, text: str) -> str:
        """Mask sensitive patterns in text."""
        # Mask tokens (long alphanumeric strings)
        import re
        text = re.sub(r'\b[A-Za-z0-9]{20,}\b', '***MASKED***', text)
        return text
    
    def _mask_value(self, value: Any) -> str:
        """Mask a sensitive value."""
        if isinstance(value, str) and len(value) > 4:
            return f"{value[:2]}***{value[-2:]}"
        return "***"


class PIIFilter(logging.Filter):
    """Filter to anonymize PII data."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Anonymize PII in log record."""
        # Hash user_id instead of logging directly
        if hasattr(record, 'user_id'):
            record.user_id_hash = self._hash_id(record.user_id)
            delattr(record, 'user_id')
        
        return True
    
    def _hash_id(self, user_id: Any) -> str:
        """Create anonymous hash of user ID."""
        return hashlib.sha256(str(user_id).encode()).hexdigest()[:16]


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__ and not k.startswith('_')
        }
        if extra_fields:
            log_data['extra'] = extra_fields
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """Add context information to log records."""
    
    def __init__(self, app_name: str, environment: str):
        super().__init__()
        self.app_name = app_name
        self.environment = environment
        self.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        record.app_name = self.app_name
        record.environment = self.environment
        record.hostname = self.hostname
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "bot.log",
    environment: str = "production",
    structured: bool = True,
    enable_pii_filter: bool = True
) -> None:
    """Configure advanced logging with security and structure.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Base name for log file
        environment: Environment name (development, staging, production)
        structured: Use JSON structured logging
        enable_pii_filter: Enable PII anonymization
    """
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Adjust log level based on environment
    if environment == "development":
        log_level = "DEBUG"
    elif environment == "production":
        log_level = "INFO"
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Set UTF-8 encoding for console
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # Error file handler (separate file for errors)
    error_handler = RotatingFileHandler(
        log_dir / f"error_{log_file}",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    # Daily rotating handler for audit logs
    audit_handler = TimedRotatingFileHandler(
        log_dir / f"audit_{log_file}",
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    audit_handler.setLevel(logging.INFO)
    
    # Formatters
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(app_name)s - %(environment)s - '
            '%(name)s - %(levelname)s - '
            '[%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    audit_handler.setFormatter(formatter)
    
    # Add filters
    context_filter = ContextFilter(app_name="telegram-bot", environment=environment)
    sensitive_filter = SensitiveDataFilter()
    
    for handler in [console_handler, file_handler, error_handler, audit_handler]:
        handler.addFilter(context_filter)
        handler.addFilter(sensitive_filter)
        if enable_pii_filter:
            handler.addFilter(PIIFilter())
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(audit_handler)
    
    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'environment': environment,
            'structured': structured,
            'pii_filter': enable_pii_filter
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger with proper configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Correlation ID support
import contextvars

correlation_id_var = contextvars.ContextVar('correlation_id', default=None)


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for request tracing."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id_var.get() or 'no-correlation-id'


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True
