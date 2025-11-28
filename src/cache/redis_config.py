"""Redis configuration management with validation."""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation.
    
    Attributes:
        is_valid: Whether configuration is valid
        errors: List of validation error messages
        warnings: List of validation warning messages
    """
    is_valid: bool
    errors: list[str]
    warnings: list[str]


@dataclass
class RedisConfig:
    """Redis configuration with validation.
    
    Attributes:
        url: Redis connection URL
        max_connections: Maximum number of connections in pool
        socket_timeout: Socket timeout in seconds
        socket_connect_timeout: Socket connect timeout in seconds
        retry_on_timeout: Whether to retry on timeout
        health_check_interval: Health check interval in seconds
        password: Redis password (optional)
        db: Redis database number
        ssl: Whether to use SSL connection
        ssl_cert_reqs: SSL certificate requirements ('required', 'optional', 'none')
        ssl_ca_certs: Path to CA certificates file
        ssl_certfile: Path to SSL certificate file
        ssl_keyfile: Path to SSL key file
        encoding: String encoding for Redis responses
        retry_on_error: Whether to retry on Redis errors
        retry_attempts: Number of retry attempts
        retry_delay: Delay between retry attempts in seconds
        connection_pool_timeout: Connection pool timeout in seconds
        max_retries: Maximum number of retries for Redis commands
        auto_close_connection_pool: Whether to automatically close connection pool
    """
    url: str
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    ssl_cert_reqs: str = 'required'
    ssl_ca_certs: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    encoding: str = 'utf-8'
    retry_on_error: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0
    connection_pool_timeout: int = 20
    max_retries: int = 3
    auto_close_connection_pool: bool = True
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """Load configuration from environment variables.
        
        Environment variables:
            REDIS_URL: Redis connection URL (required)
            REDIS_MAX_CONNECTIONS: Maximum connections (default: 10)
            REDIS_SOCKET_TIMEOUT: Socket timeout in seconds (default: 5)
            REDIS_SOCKET_CONNECT_TIMEOUT: Connect timeout in seconds (default: 5)
            REDIS_RETRY_ON_TIMEOUT: Retry on timeout (default: true)
            REDIS_HEALTH_CHECK_INTERVAL: Health check interval (default: 30)
            REDIS_PASSWORD: Redis password (optional)
            REDIS_DB: Redis database number (default: 0)
            REDIS_SSL: Use SSL connection (default: false)
            REDIS_SSL_CERT_REQS: SSL certificate requirements (default: required)
            REDIS_SSL_CA_CERTS: Path to CA certificates file (optional)
            REDIS_SSL_CERTFILE: Path to SSL certificate file (optional)
            REDIS_SSL_KEYFILE: Path to SSL key file (optional)
            REDIS_ENCODING: String encoding (default: utf-8)
            REDIS_RETRY_ON_ERROR: Retry on Redis errors (default: true)
            REDIS_RETRY_ATTEMPTS: Number of retry attempts (default: 3)
            REDIS_RETRY_DELAY: Delay between retries in seconds (default: 1.0)
            REDIS_CONNECTION_POOL_TIMEOUT: Connection pool timeout (default: 20)
            REDIS_MAX_RETRIES: Maximum command retries (default: 3)
            REDIS_AUTO_CLOSE_CONNECTION_POOL: Auto close connection pool (default: true)
        
        Returns:
            RedisConfig instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        url = os.getenv('REDIS_URL')
        if not url:
            raise ValueError(
                "REDIS_URL environment variable is required. "
                "Example: redis://localhost:6379/0"
            )
        
        try:
            max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '10'))
        except ValueError:
            logger.warning("Invalid REDIS_MAX_CONNECTIONS, using default: 10")
            max_connections = 10
        
        try:
            socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
        except ValueError:
            logger.warning("Invalid REDIS_SOCKET_TIMEOUT, using default: 5")
            socket_timeout = 5
        
        try:
            socket_connect_timeout = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
        except ValueError:
            logger.warning("Invalid REDIS_SOCKET_CONNECT_TIMEOUT, using default: 5")
            socket_connect_timeout = 5
        
        retry_on_timeout_str = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower()
        retry_on_timeout = retry_on_timeout_str in ('true', '1', 'yes')
        
        try:
            health_check_interval = int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30'))
        except ValueError:
            logger.warning("Invalid REDIS_HEALTH_CHECK_INTERVAL, using default: 30")
            health_check_interval = 30
        
        password = os.getenv('REDIS_PASSWORD')
        
        try:
            db = int(os.getenv('REDIS_DB', '0'))
        except ValueError:
            logger.warning("Invalid REDIS_DB, using default: 0")
            db = 0
        
        ssl_str = os.getenv('REDIS_SSL', 'false').lower()
        ssl = ssl_str in ('true', '1', 'yes')
        
        ssl_cert_reqs = os.getenv('REDIS_SSL_CERT_REQS', 'required')
        ssl_ca_certs = os.getenv('REDIS_SSL_CA_CERTS')
        ssl_certfile = os.getenv('REDIS_SSL_CERTFILE')
        ssl_keyfile = os.getenv('REDIS_SSL_KEYFILE')
        
        encoding = os.getenv('REDIS_ENCODING', 'utf-8')
        
        retry_on_error_str = os.getenv('REDIS_RETRY_ON_ERROR', 'true').lower()
        retry_on_error = retry_on_error_str in ('true', '1', 'yes')
        
        try:
            retry_attempts = int(os.getenv('REDIS_RETRY_ATTEMPTS', '3'))
        except ValueError:
            logger.warning("Invalid REDIS_RETRY_ATTEMPTS, using default: 3")
            retry_attempts = 3
        
        try:
            retry_delay = float(os.getenv('REDIS_RETRY_DELAY', '1.0'))
        except ValueError:
            logger.warning("Invalid REDIS_RETRY_DELAY, using default: 1.0")
            retry_delay = 1.0
        
        try:
            connection_pool_timeout = int(os.getenv('REDIS_CONNECTION_POOL_TIMEOUT', '20'))
        except ValueError:
            logger.warning("Invalid REDIS_CONNECTION_POOL_TIMEOUT, using default: 20")
            connection_pool_timeout = 20
        
        try:
            max_retries = int(os.getenv('REDIS_MAX_RETRIES', '3'))
        except ValueError:
            logger.warning("Invalid REDIS_MAX_RETRIES, using default: 3")
            max_retries = 3
        
        auto_close_str = os.getenv('REDIS_AUTO_CLOSE_CONNECTION_POOL', 'true').lower()
        auto_close_connection_pool = auto_close_str in ('true', '1', 'yes')
        
        config = cls(
            url=url,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            health_check_interval=health_check_interval,
            password=password,
            db=db,
            ssl=ssl,
            ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs,
            ssl_certfile=ssl_certfile,
            ssl_keyfile=ssl_keyfile,
            encoding=encoding,
            retry_on_error=retry_on_error,
            retry_attempts=retry_attempts,
            retry_delay=retry_delay,
            connection_pool_timeout=connection_pool_timeout,
            max_retries=max_retries,
            auto_close_connection_pool=auto_close_connection_pool
        )
        
        logger.info("Redis configuration loaded from environment")
        return config
    
    def validate(self) -> ValidationResult:
        """Validate configuration.
        
        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        
        # Validate URL
        if not self.url:
            errors.append("Redis URL is required")
        else:
            try:
                parsed = urlparse(self.url)
                
                if parsed.scheme not in ('redis', 'rediss'):
                    errors.append(
                        f"Invalid Redis URL scheme: {parsed.scheme}. "
                        f"Must be 'redis' or 'rediss'"
                    )
                
                if not parsed.hostname:
                    errors.append("Redis URL must include hostname")
                
                if parsed.port and (parsed.port < 1 or parsed.port > 65535):
                    errors.append(f"Invalid Redis port: {parsed.port}")
                    
            except Exception as e:
                errors.append(f"Invalid Redis URL format: {e}")
        
        # Validate max_connections
        if self.max_connections < 1:
            errors.append(
                f"max_connections must be at least 1, got: {self.max_connections}"
            )
        elif self.max_connections > 100:
            warnings.append(
                f"max_connections is very high ({self.max_connections}). "
                f"Consider using a lower value for better resource management."
            )
        
        # Validate timeouts
        if self.socket_timeout < 1:
            errors.append(
                f"socket_timeout must be at least 1 second, got: {self.socket_timeout}"
            )
        elif self.socket_timeout > 60:
            warnings.append(
                f"socket_timeout is very high ({self.socket_timeout}s). "
                f"This may cause long delays on connection issues."
            )
        
        if self.socket_connect_timeout < 1:
            errors.append(
                f"socket_connect_timeout must be at least 1 second, "
                f"got: {self.socket_connect_timeout}"
            )
        elif self.socket_connect_timeout > 30:
            warnings.append(
                f"socket_connect_timeout is very high ({self.socket_connect_timeout}s). "
                f"Consider using a lower value."
            )
        
        # Validate health_check_interval
        if self.health_check_interval < 5:
            warnings.append(
                f"health_check_interval is very low ({self.health_check_interval}s). "
                f"This may cause unnecessary load."
            )
        elif self.health_check_interval > 300:
            warnings.append(
                f"health_check_interval is very high ({self.health_check_interval}s). "
                f"Connection issues may not be detected quickly."
            )
        
        # Validate database number
        if self.db < 0 or self.db > 15:
            errors.append(
                f"Redis database number must be between 0 and 15, got: {self.db}"
            )
        
        # Validate SSL settings
        if self.ssl:
            if self.ssl_cert_reqs not in ('required', 'optional', 'none'):
                errors.append(
                    f"ssl_cert_reqs must be 'required', 'optional', or 'none', got: {self.ssl_cert_reqs}"
                )
            
            if self.ssl_cert_reqs == 'required' and not self.ssl_ca_certs:
                warnings.append(
                    "SSL is enabled with required certificates but no CA certificates path provided"
                )
        
        # Validate retry settings
        if self.retry_attempts < 0:
            errors.append(
                f"retry_attempts must be non-negative, got: {self.retry_attempts}"
            )
        
        if self.retry_delay < 0:
            errors.append(
                f"retry_delay must be non-negative, got: {self.retry_delay}"
            )
        
        if self.connection_pool_timeout < 1:
            errors.append(
                f"connection_pool_timeout must be at least 1 second, got: {self.connection_pool_timeout}"
            )
        
        if self.max_retries < 0:
            errors.append(
                f"max_retries must be non-negative, got: {self.max_retries}"
            )
        
        # Validate encoding
        try:
            "".encode(self.encoding)
        except LookupError:
            errors.append(f"Invalid encoding: {self.encoding}")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def get_connection_params(self) -> dict:
        """Get connection parameters for Redis client.
        
        Returns:
            Dictionary of connection parameters
        """
        params = {
            'max_connections': self.max_connections,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'retry_on_timeout': self.retry_on_timeout,
            'health_check_interval': self.health_check_interval,
            'encoding': self.encoding,
            'decode_responses': True,
            'retry_on_error': self.retry_on_error,
            'max_retries': self.max_retries
        }
        
        if self.password:
            params['password'] = self.password
        
        if self.ssl:
            params['ssl'] = True
            params['ssl_cert_reqs'] = self.ssl_cert_reqs
            if self.ssl_ca_certs:
                params['ssl_ca_certs'] = self.ssl_ca_certs
            if self.ssl_certfile:
                params['ssl_certfile'] = self.ssl_certfile
            if self.ssl_keyfile:
                params['ssl_keyfile'] = self.ssl_keyfile
        
        return params
    
    def __repr__(self) -> str:
        """String representation of config (hides password).
        
        Returns:
            String representation
        """
        # Parse URL to hide password
        try:
            parsed = urlparse(self.url)
            safe_url = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                safe_url += f":{parsed.port}"
            if parsed.path:
                safe_url += parsed.path
        except:
            safe_url = "invalid_url"
        
        return (
            f"RedisConfig(url='{safe_url}', "
            f"max_connections={self.max_connections}, "
            f"socket_timeout={self.socket_timeout}s, "
            f"db={self.db}, "
            f"ssl={self.ssl})"
        )
