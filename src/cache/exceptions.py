"""Cache-specific exceptions."""


class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass


class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""
    pass


class CacheOperationError(CacheError):
    """Raised when cache operation fails."""
    pass


class CacheConfigurationError(CacheError):
    """Raised when cache configuration is invalid."""
    pass


class CacheTimeoutError(CacheError):
    """Raised when cache operation times out."""
    pass
