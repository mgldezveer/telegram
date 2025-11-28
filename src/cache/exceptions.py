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


class CacheSerializationError(CacheError):
    """Raised when cache value serialization/deserialization fails."""
    pass


class CacheKeyError(CacheError):
    """Raised when cache key is invalid or malformed."""
    pass


class CacheCapacityError(CacheError):
    """Raised when cache capacity is exceeded."""
    pass


class CacheValidationError(CacheError):
    """Raised when cached value fails validation."""
    pass


class CacheInconsistencyError(CacheError):
    """Raised when cache state becomes inconsistent."""
    pass


class CacheBackendError(CacheError):
    """Raised when cache backend encounters an error."""
    pass
