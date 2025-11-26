# Design Document

## Overview

This document outlines the technical design for improving the AI Content Bot infrastructure by addressing Redis connectivity issues, Python version compatibility, and PTB ConversationHandler warnings. The solution focuses on graceful degradation, proper configuration management, and adherence to library best practices.

## Architecture

### Current Architecture Issues

1. **Redis Connection**: Hard failure when Redis is unavailable, no graceful fallback
2. **Python Version**: No version checking at startup, deprecated warnings in logs
3. **ConversationHandler**: Missing `per_message=True` parameter causing PTB warnings

### Improved Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Startup                      │
│  1. Python Version Check                                     │
│  2. Environment Validation                                   │
│  3. Database Initialization                                  │
│  4. Redis Connection (with fallback)                         │
│  5. Bot Controller Initialization                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Cache Layer                             │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ Redis Cache  │◄────────┤ Cache Facade │                 │
│  │  (Primary)   │         │              │                 │
│  └──────────────┘         └──────────────┘                 │
│         │                        │                           │
│         │ (fallback)             │                           │
│         ▼                        ▼                           │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ Memory Cache │         │  LLM Cache   │                 │
│  │  (Fallback)  │         │   Service    │                 │
│  └──────────────┘         └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Conversation Handlers                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ConversationHandler (per_message=True)               │  │
│  │  - Channel Registration                               │  │
│  │  - Custom Theme Input                                 │  │
│  │  - Post Editing                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Python Version Checker

**Purpose**: Validate Python version at startup and provide clear warnings

**Interface**:
```python
class PythonVersionChecker:
    """Check and validate Python version."""
    
    MINIMUM_VERSION = (3, 10)
    RECOMMENDED_VERSION = (3, 11)
    
    @staticmethod
    def check_version() -> VersionCheckResult:
        """Check current Python version.
        
        Returns:
            VersionCheckResult with status and message
        """
        pass
    
    @staticmethod
    def get_version_info() -> dict:
        """Get detailed version information."""
        pass
```

**VersionCheckResult**:
```python
@dataclass
class VersionCheckResult:
    is_compatible: bool
    current_version: tuple
    message: str
    severity: str  # 'ok', 'warning', 'error'
```

### 2. Enhanced Cache Service

**Purpose**: Provide unified caching interface with automatic fallback

**Interface**:
```python
class CacheService:
    """Enhanced caching service with fallback support."""
    
    def __init__(self, redis_url: str, fallback_enabled: bool = True):
        self.redis: Optional[redis.Redis] = None
        self.fallback_cache: Optional[MemoryCache] = None
        self.is_redis_available: bool = False
    
    async def connect(self) -> ConnectionResult:
        """Connect to Redis with fallback to memory cache."""
        pass
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or fallback)."""
        pass
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache (Redis or fallback)."""
        pass
    
    async def health_check(self) -> CacheHealthStatus:
        """Check cache health and return status."""
        pass
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        pass
```

**MemoryCache** (Fallback):
```python
class MemoryCache:
    """In-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        pass
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in memory cache with TTL."""
        pass
    
    async def cleanup_expired(self):
        """Remove expired entries."""
        pass
```

### 3. Redis Configuration Manager

**Purpose**: Manage Redis connection configuration and retry logic

**Interface**:
```python
class RedisConfig:
    """Redis configuration with validation."""
    
    url: str
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """Load configuration from environment variables."""
        pass
    
    def validate(self) -> ValidationResult:
        """Validate configuration."""
        pass
```

### 4. Conversation Handler Factory

**Purpose**: Create properly configured ConversationHandlers

**Interface**:
```python
class ConversationHandlerFactory:
    """Factory for creating properly configured ConversationHandlers."""
    
    @staticmethod
    def create_handler(
        name: str,
        entry_points: List,
        states: Dict,
        fallbacks: List,
        timeout: int = 300,
        per_message: bool = True,  # Fix for PTB warning
        per_chat: bool = True,
        per_user: bool = True
    ) -> ConversationHandler:
        """Create ConversationHandler with proper configuration.
        
        Args:
            name: Handler name for logging
            entry_points: Entry point handlers
            states: State handlers mapping
            fallbacks: Fallback handlers
            timeout: Conversation timeout in seconds
            per_message: Track per message (required for CallbackQueryHandler)
            per_chat: Track per chat
            per_user: Track per user
            
        Returns:
            Properly configured ConversationHandler
        """
        pass
```

### 5. Health Check Service

**Purpose**: Monitor system health including Redis connectivity

**Interface**:
```python
class HealthCheckService:
    """System health monitoring."""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
    
    async def get_health_status(self) -> HealthStatus:
        """Get overall system health status."""
        pass
    
    async def get_redis_status(self) -> RedisStatus:
        """Get Redis-specific status."""
        pass
```

**HealthStatus**:
```python
@dataclass
class HealthStatus:
    status: str  # 'healthy', 'degraded', 'unhealthy'
    components: Dict[str, ComponentStatus]
    timestamp: datetime
    
@dataclass
class ComponentStatus:
    name: str
    status: str
    message: str
    details: Optional[dict] = None
```

## Data Models

### Cache Entry
```python
@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now() > self.expires_at
```

### Cache Statistics
```python
@dataclass
class CacheStats:
    """Cache statistics."""
    backend: str  # 'redis' or 'memory'
    total_keys: int
    hit_rate: float
    miss_rate: float
    memory_usage: Optional[int]  # bytes, None for Redis
    uptime: timedelta
```

### Connection Result
```python
@dataclass
class ConnectionResult:
    """Result of cache connection attempt."""
    success: bool
    backend: str  # 'redis' or 'memory'
    message: str
    error: Optional[Exception] = None
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Cache Fallback Consistency
*For any* cache operation (get/set/delete), if Redis is unavailable, the operation should complete successfully using the memory cache fallback without raising exceptions.
**Validates: Requirements 1.4, 6.1**

### Property 2: Version Check Determinism
*For any* Python version tuple, the version checker should consistently return the same compatibility result (compatible/incompatible) across multiple invocations.
**Validates: Requirements 3.1, 3.2**

### Property 3: ConversationHandler Configuration Completeness
*For any* ConversationHandler created by the factory, if it contains CallbackQueryHandler in its states, then per_message must be set to True.
**Validates: Requirements 4.1, 4.2**

### Property 4: Redis Reconnection Idempotence
*For any* cache service instance, calling connect() multiple times should result in a single active connection without creating connection leaks.
**Validates: Requirements 6.3**

### Property 5: Health Check Non-Interference
*For any* health check execution, the check should complete within a bounded time (< 5 seconds) and should not block or interfere with normal bot operations.
**Validates: Requirements 5.4**

### Property 6: Cache TTL Preservation
*For any* cached value with TTL, if stored in Redis and then Redis becomes unavailable causing fallback to memory cache, the remaining TTL should be preserved within a reasonable margin (±10 seconds).
**Validates: Requirements 1.3, 6.2**

### Property 7: Configuration Validation Completeness
*For any* Redis configuration, if any required parameter (url, max_connections, timeout) is invalid or missing, the validation should fail with a specific error message identifying the problematic parameter.
**Validates: Requirements 2.3**

## Error Handling

### Redis Connection Errors

**Strategy**: Graceful degradation with fallback

```python
async def connect_with_fallback(self) -> ConnectionResult:
    """Connect to Redis with automatic fallback."""
    try:
        # Attempt Redis connection
        self.redis = await self._connect_redis()
        await self.redis.ping()
        self.is_redis_available = True
        logger.info("✅ Connected to Redis")
        return ConnectionResult(
            success=True,
            backend='redis',
            message='Connected to Redis successfully'
        )
    except redis.ConnectionError as e:
        logger.warning(f"⚠️ Redis unavailable: {e}")
        logger.info("Falling back to memory cache")
        self.fallback_cache = MemoryCache()
        self.is_redis_available = False
        return ConnectionResult(
            success=True,
            backend='memory',
            message='Using memory cache (Redis unavailable)',
            error=e
        )
    except Exception as e:
        logger.error(f"❌ Cache initialization failed: {e}")
        raise
```

### Python Version Errors

**Strategy**: Early detection with clear messaging

```python
def check_version_at_startup():
    """Check Python version before starting bot."""
    result = PythonVersionChecker.check_version()
    
    if result.severity == 'error':
        logger.error(result.message)
        sys.exit(1)
    elif result.severity == 'warning':
        logger.warning(result.message)
        logger.warning("Bot will continue but upgrade is recommended")
    else:
        logger.info(result.message)
```

### ConversationHandler Errors

**Strategy**: Validation at creation time

```python
def create_handler(...) -> ConversationHandler:
    """Create handler with validation."""
    # Validate configuration
    if self._has_callback_handlers(states) and not per_message:
        logger.warning(
            f"ConversationHandler '{name}' contains CallbackQueryHandler "
            f"but per_message=False. Setting per_message=True to avoid warnings."
        )
        per_message = True
    
    return ConversationHandler(
        entry_points=entry_points,
        states=states,
        fallbacks=fallbacks,
        conversation_timeout=timeout,
        per_message=per_message,
        per_chat=per_chat,
        per_user=per_user,
        name=name
    )
```

## Testing Strategy

### Unit Tests

**Cache Service Tests**:
- Test Redis connection success/failure
- Test fallback activation
- Test cache operations in both modes
- Test TTL expiration
- Test memory cache cleanup

**Version Checker Tests**:
- Test version comparison logic
- Test warning message generation
- Test compatibility detection

**ConversationHandler Factory Tests**:
- Test handler creation with various configurations
- Test automatic per_message correction
- Test validation logic

### Property-Based Tests

**Property Test Framework**: pytest with Hypothesis

**Test Configuration**:
- Minimum 100 iterations per property
- Use random data generators for cache keys, values, TTLs
- Use version tuple generators for version checking

**Property 1 Test**:
```python
@given(
    key=st.text(min_size=1, max_size=100),
    value=st.text(),
    ttl=st.integers(min_value=1, max_value=3600)
)
@settings(max_examples=100)
async def test_cache_fallback_consistency(key, value, ttl):
    """**Feature: infrastructure-improvements, Property 1: Cache Fallback Consistency**
    
    Test that cache operations work with both Redis and memory fallback.
    """
    cache = CacheService(redis_url="redis://invalid:6379", fallback_enabled=True)
    await cache.connect()  # Will fallback to memory
    
    # Should not raise exception
    await cache.set(key, value, ttl)
    result = await cache.get(key)
    
    assert result == value
```

**Property 2 Test**:
```python
@given(
    version=st.tuples(
        st.integers(min_value=3, max_value=4),
        st.integers(min_value=0, max_value=20)
    )
)
@settings(max_examples=100)
def test_version_check_determinism(version):
    """**Feature: infrastructure-improvements, Property 2: Version Check Determinism**
    
    Test that version checking is deterministic.
    """
    checker = PythonVersionChecker()
    
    # Check multiple times
    result1 = checker.check_version_tuple(version)
    result2 = checker.check_version_tuple(version)
    result3 = checker.check_version_tuple(version)
    
    # All results should be identical
    assert result1.is_compatible == result2.is_compatible == result3.is_compatible
    assert result1.severity == result2.severity == result3.severity
```

**Property 3 Test**:
```python
@given(
    has_callback_handler=st.booleans(),
    per_message_input=st.booleans()
)
@settings(max_examples=100)
def test_conversation_handler_configuration(has_callback_handler, per_message_input):
    """**Feature: infrastructure-improvements, Property 3: ConversationHandler Configuration Completeness**
    
    Test that ConversationHandlers with CallbackQueryHandler have per_message=True.
    """
    factory = ConversationHandlerFactory()
    
    states = {}
    if has_callback_handler:
        states[0] = [CallbackQueryHandler(lambda u, c: None, pattern="test")]
    else:
        states[0] = [MessageHandler(filters.TEXT, lambda u, c: None)]
    
    handler = factory.create_handler(
        name="test",
        entry_points=[],
        states=states,
        fallbacks=[],
        per_message=per_message_input
    )
    
    # If has callback handler, per_message must be True
    if has_callback_handler:
        assert handler.per_message is True
```

### Integration Tests

- Test full bot startup with Redis unavailable
- Test Redis reconnection after initial failure
- Test health check endpoint responses
- Test conversation handlers in real scenarios

### Edge Cases

- Redis connection timeout
- Redis authentication failure
- Memory cache overflow
- Concurrent cache access
- Python version edge cases (3.9.x, 3.10.0, 3.13+)
- ConversationHandler with mixed handler types

## Implementation Notes

### Redis Installation (Windows)

**Option 1: WSL (Recommended)**:
```bash
# Install WSL
wsl --install

# Install Redis in WSL
sudo apt update
sudo apt install redis-server

# Start Redis
sudo service redis-server start
```

**Option 2: Docker**:
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

**Option 3: Memurai (Windows Native)**:
- Download from https://www.memurai.com/
- Install and run as Windows service

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
REDIS_HEALTH_CHECK_INTERVAL=30

# Cache Configuration
CACHE_FALLBACK_ENABLED=true
CACHE_MEMORY_MAX_SIZE=1000
CACHE_DEFAULT_TTL=300

# Python Version
PYTHON_MIN_VERSION=3.10
PYTHON_VERSION_CHECK_ENABLED=true
```

### Migration Path

1. **Phase 1**: Implement enhanced cache service with fallback
2. **Phase 2**: Add Python version checking
3. **Phase 3**: Fix ConversationHandler configurations
4. **Phase 4**: Add health check endpoint
5. **Phase 5**: Add comprehensive tests

### Performance Considerations

- Memory cache should have size limits to prevent memory leaks
- Implement LRU eviction for memory cache
- Redis connection pooling for better performance
- Health checks should be lightweight and non-blocking
- Cache cleanup should run periodically in background

### Backward Compatibility

- Existing code using `cache.get()` and `cache.set()` will work unchanged
- Fallback is transparent to calling code
- No breaking changes to public APIs
- Configuration is additive (new env vars are optional)
