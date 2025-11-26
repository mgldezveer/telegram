"""Examples of proper logging practices."""

import logging
from typing import Optional
import time
from functools import wraps

logger = logging.getLogger(__name__)


# ============================================================================
# 1. ПРАВИЛЬНЫЕ УРОВНИ ЛОГОВ
# ============================================================================

def example_log_levels():
    """Примеры правильного использования уровней логов."""
    
    # DEBUG - детальная информация для отладки
    logger.debug(
        "Processing user request",
        extra={
            'user_id_hash': 'abc123',  # Хешированный ID
            'action': 'channel_registration',
            'step': 1
        }
    )
    
    # INFO - важные события в нормальной работе
    logger.info(
        "Channel registered successfully",
        extra={
            'channel_id': 12345,
            'channel_name': 'Tech News'
        }
    )
    
    # WARNING - что-то необычное, но не критичное
    logger.warning(
        "Rate limit approaching",
        extra={
            'current_requests': 95,
            'limit': 100,
            'window': '1 minute'
        }
    )
    
    # ERROR - ошибка, но приложение продолжает работать
    logger.error(
        "Failed to publish post",
        extra={
            'channel_id': 12345,
            'post_id': 67890,
            'error_type': 'NetworkError',
            'retry_count': 2
        }
    )
    
    # CRITICAL - критическая ошибка, требует немедленного внимания
    logger.critical(
        "Database connection lost",
        extra={
            'database': 'postgresql',
            'host': 'db.example.com',
            'last_successful_query': '2024-01-01 12:00:00'
        }
    )


# ============================================================================
# 2. STRUCTURED LOGGING
# ============================================================================

def example_structured_logging():
    """Примеры структурированного логирования."""
    
    # ❌ ПЛОХО - строковая интерполяция
    user_id = 12345
    action = "login"
    logger.info(f"User {user_id} performed {action}")
    
    # ✅ ХОРОШО - structured logging
    logger.info(
        "User action performed",
        extra={
            'user_id_hash': hash_user_id(user_id),
            'action': action,
            'timestamp': time.time(),
            'ip_address': '192.168.1.1',  # Можно логировать IP
            'user_agent': 'TelegramBot/1.0'
        }
    )


# ============================================================================
# 3. EXCEPTION LOGGING
# ============================================================================

def example_exception_logging():
    """Примеры правильного логирования исключений."""
    
    try:
        # Какая-то операция
        result = risky_operation()
    except ValueError as e:
        # ❌ ПЛОХО - теряется traceback
        logger.error(f"Value error: {e}")
    except TypeError as e:
        # ✅ ХОРОШО - используем exception() для полного traceback
        logger.exception(
            "Type error in risky operation",
            extra={
                'operation': 'risky_operation',
                'input_type': type(e).__name__
            }
        )
    except Exception as e:
        # ✅ ХОРОШО - exc_info=True для traceback
        logger.error(
            "Unexpected error in risky operation",
            exc_info=True,
            extra={
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        )


# ============================================================================
# 4. PERFORMANCE LOGGING
# ============================================================================

def log_slow_operation(threshold_seconds: float = 1.0):
    """Декоратор для логирования медленных операций."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Логируем только медленные операции
                if duration > threshold_seconds:
                    logger.warning(
                        f"Slow operation detected: {func.__name__}",
                        extra={
                            'function': func.__name__,
                            'duration_seconds': duration,
                            'threshold_seconds': threshold_seconds,
                            'args_count': len(args),
                            'kwargs_keys': list(kwargs.keys())
                        }
                    )
                else:
                    logger.debug(
                        f"Operation completed: {func.__name__}",
                        extra={
                            'function': func.__name__,
                            'duration_seconds': duration
                        }
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.exception(
                    f"Operation failed: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'duration_seconds': duration,
                        'error_type': type(e).__name__
                    }
                )
                raise
        
        return wrapper
    return decorator


# Использование
@log_slow_operation(threshold_seconds=2.0)
async def generate_content(channel_id: int, theme: str):
    """Generate content with performance logging."""
    # ... implementation
    pass


# ============================================================================
# 5. CONTEXT LOGGING
# ============================================================================

class RequestContext:
    """Контекст запроса для логирования."""
    
    def __init__(self, user_id: int, action: str):
        self.user_id_hash = hash_user_id(user_id)
        self.action = action
        self.start_time = time.time()
        self.correlation_id = generate_correlation_id()
    
    def log_start(self):
        """Логировать начало операции."""
        logger.info(
            f"Starting {self.action}",
            extra={
                'correlation_id': self.correlation_id,
                'user_id_hash': self.user_id_hash,
                'action': self.action,
                'timestamp': self.start_time
            }
        )
    
    def log_end(self, success: bool = True, error: Optional[Exception] = None):
        """Логировать завершение операции."""
        duration = time.time() - self.start_time
        
        if success:
            logger.info(
                f"Completed {self.action}",
                extra={
                    'correlation_id': self.correlation_id,
                    'user_id_hash': self.user_id_hash,
                    'action': self.action,
                    'duration_seconds': duration,
                    'success': True
                }
            )
        else:
            logger.error(
                f"Failed {self.action}",
                extra={
                    'correlation_id': self.correlation_id,
                    'user_id_hash': self.user_id_hash,
                    'action': self.action,
                    'duration_seconds': duration,
                    'success': False,
                    'error_type': type(error).__name__ if error else 'Unknown',
                    'error_message': str(error) if error else 'Unknown'
                },
                exc_info=error is not None
            )


# Использование
async def handle_user_action(user_id: int, action: str):
    """Handle user action with context logging."""
    ctx = RequestContext(user_id, action)
    ctx.log_start()
    
    try:
        # Perform action
        result = await perform_action(action)
        ctx.log_end(success=True)
        return result
    except Exception as e:
        ctx.log_end(success=False, error=e)
        raise


# ============================================================================
# 6. SECURITY LOGGING
# ============================================================================

def log_security_event(event_type: str, severity: str, details: dict):
    """Логировать события безопасности."""
    logger.warning(
        f"Security event: {event_type}",
        extra={
            'event_type': event_type,
            'severity': severity,
            'timestamp': time.time(),
            **details
        }
    )


# Примеры
def example_security_logging():
    """Примеры логирования событий безопасности."""
    
    # Неудачная попытка входа
    log_security_event(
        event_type='failed_authentication',
        severity='medium',
        details={
            'user_id_hash': 'abc123',
            'ip_address': '192.168.1.1',
            'attempt_count': 3
        }
    )
    
    # Подозрительная активность
    log_security_event(
        event_type='suspicious_activity',
        severity='high',
        details={
            'user_id_hash': 'abc123',
            'action': 'mass_message_sending',
            'message_count': 100,
            'time_window_seconds': 60
        }
    )
    
    # Доступ к защищенному ресурсу
    log_security_event(
        event_type='admin_access',
        severity='info',
        details={
            'user_id_hash': 'admin123',
            'resource': 'user_database',
            'action': 'read'
        }
    )


# ============================================================================
# 7. AUDIT LOGGING
# ============================================================================

def log_audit_event(action: str, user_id: int, resource: str, details: dict):
    """Логировать события аудита."""
    audit_logger = logging.getLogger('audit')
    audit_logger.info(
        f"Audit: {action}",
        extra={
            'action': action,
            'user_id_hash': hash_user_id(user_id),
            'resource': resource,
            'timestamp': time.time(),
            **details
        }
    )


# Примеры
def example_audit_logging():
    """Примеры аудит-логирования."""
    
    # Создание канала
    log_audit_event(
        action='channel_created',
        user_id=12345,
        resource='channel',
        details={
            'channel_id': 67890,
            'channel_name': 'Tech News'
        }
    )
    
    # Удаление поста
    log_audit_event(
        action='post_deleted',
        user_id=12345,
        resource='post',
        details={
            'post_id': 111,
            'channel_id': 67890,
            'reason': 'user_request'
        }
    )
    
    # Изменение настроек
    log_audit_event(
        action='settings_updated',
        user_id=12345,
        resource='settings',
        details={
            'setting_key': 'auto_publish',
            'old_value': False,
            'new_value': True
        }
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_user_id(user_id: int) -> str:
    """Hash user ID for privacy."""
    import hashlib
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:16]


def generate_correlation_id() -> str:
    """Generate unique correlation ID."""
    import uuid
    return str(uuid.uuid4())


def risky_operation():
    """Dummy risky operation."""
    pass


async def perform_action(action: str):
    """Dummy action performer."""
    pass
