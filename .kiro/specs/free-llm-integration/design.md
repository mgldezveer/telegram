# Design Document: Free LLM Integration

## Overview

Система интеграции бесплатных LLM провайдеров с автоматическим управлением лимитами, кэшированием и fallback механизмом. Архитектура построена на принципах расширяемости и надежности.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot Interface                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM Manager (Orchestrator)                 │
│  - Provider Selection                                        │
│  - Rate Limit Management                                     │
│  - Fallback Logic                                           │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
            ▼                                 ▼
┌───────────────────────┐         ┌──────────────────────────┐
│   Cache Layer         │         │   Monitoring Service     │
│   - Redis Cache       │         │   - Metrics Collection   │
│   - Semantic Cache    │         │   - Usage Tracking       │
└───────────────────────┘         └──────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Provider Adapters                         │
├──────────────────┬──────────────────┬───────────────────────┤
│   Groq Adapter   │  Gemini Adapter  │  HuggingFace Adapter │
└──────────────────┴──────────────────┴───────────────────────┘
            │                │                │
            ▼                ▼                ▼
┌──────────────────┬──────────────────┬───────────────────────┐
│   Groq API       │   Gemini API     │   HuggingFace API    │
└──────────────────┴──────────────────┴───────────────────────┘
```

## Components and Interfaces

### 1. LLM Manager

**Responsibilities:**
- Управление провайдерами
- Выбор оптимального провайдера
- Обработка fallback
- Управление rate limits

**Interface:**
```python
class LLMManager:
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> LLMResponse
    
    async def get_available_providers(self) -> List[str]
    
    async def get_provider_status(self, provider: str) -> ProviderStatus
    
    async def switch_provider(self, provider: str) -> bool
```

### 2. Provider Adapter (Abstract Base)

**Interface:**
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str
    
    @abstractmethod
    async def check_availability(self) -> bool
    
    @abstractmethod
    def get_rate_limit_info(self) -> RateLimitInfo
    
    @abstractmethod
    def get_remaining_quota(self) -> int
```

### 3. Groq Provider

**Configuration:**
```python
GROQ_API_KEY: str
GROQ_MODEL: str = "llama3-70b-8192"  # или mixtral-8x7b-32768
GROQ_MAX_TOKENS: int = 8192
GROQ_RATE_LIMIT: int = 30  # requests per minute
```

**Features:**
- Очень быстрая генерация (< 1 сек)
- Бесплатный tier: 30 req/min
- Модели: Llama 3, Mixtral

### 4. Google Gemini Provider

**Configuration:**
```python
GEMINI_API_KEY: str
GEMINI_MODEL: str = "gemini-pro"
GEMINI_MAX_TOKENS: int = 2048
GEMINI_DAILY_LIMIT: int = 60  # requests per day (free tier)
```

**Features:**
- Качественная генерация
- Бесплатный tier: 60 req/day
- Safety settings

### 5. Hugging Face Provider

**Configuration:**
```python
HF_API_KEY: str
HF_MODEL: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
HF_MAX_TOKENS: int = 1024
HF_RATE_LIMIT: int = 1000  # requests per hour
```

**Features:**
- Множество открытых моделей
- Бесплатный tier: 1000 req/hour
- Может быть медленнее

### 6. Cache Service

**Interface:**
```python
class CacheService:
    async def get(self, key: str) -> Optional[str]
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: int = 3600
    ) -> bool
    
    async def get_semantic(
        self,
        prompt: str,
        similarity_threshold: float = 0.95
    ) -> Optional[str]
    
    def generate_cache_key(
        self,
        prompt: str,
        params: dict
    ) -> str
```

**Cache Strategy:**
- Exact match cache (Redis)
- TTL: 1 hour
- LRU eviction
- Semantic similarity cache (optional)

### 7. Rate Limit Manager

**Interface:**
```python
class RateLimitManager:
    async def check_limit(
        self,
        provider: str
    ) -> bool
    
    async def record_request(
        self,
        provider: str,
        tokens_used: int
    ) -> None
    
    async def get_usage_stats(
        self,
        provider: str
    ) -> UsageStats
    
    async def reset_limits(
        self,
        provider: str
    ) -> None
```

**Storage:**
- Redis для счетчиков
- Sliding window algorithm
- Автоматический reset по расписанию

## Data Models

### LLMResponse

```python
@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    tokens_used: int
    generation_time: float
    cached: bool
    metadata: Dict[str, Any]
```

### ProviderStatus

```python
@dataclass
class ProviderStatus:
    name: str
    available: bool
    rate_limit_remaining: int
    rate_limit_reset_at: datetime
    last_error: Optional[str]
    avg_response_time: float
```

### RateLimitInfo

```python
@dataclass
class RateLimitInfo:
    requests_per_minute: Optional[int]
    requests_per_hour: Optional[int]
    requests_per_day: Optional[int]
    tokens_per_minute: Optional[int]
    current_usage: int
    reset_at: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Provider fallback chain
*For any* generation request, if the primary provider fails, the system should automatically try the next available provider until success or all providers are exhausted.
**Validates: Requirements 1.3**

### Property 2: Rate limit enforcement
*For any* provider, when the rate limit is reached, the system should not send additional requests until the limit resets.
**Validates: Requirements 5.2**

### Property 3: Cache consistency
*For any* identical prompt with same parameters, the system should return the same cached result within the TTL period.
**Validates: Requirements 6.1**

### Property 4: Retry with exponential backoff
*For any* failed request, the system should retry with exponentially increasing delays (1s, 2s, 4s) up to 3 attempts.
**Validates: Requirements 7.1**

### Property 5: Provider switching on rate limit
*For any* provider that returns a rate limit error, the system should immediately switch to the next available provider without retry.
**Validates: Requirements 7.2**

### Property 6: Token counting accuracy
*For any* completed request, the system should accurately record the number of tokens used for rate limit tracking.
**Validates: Requirements 5.1**

### Property 7: Configuration validation
*For any* provider configuration, the system should validate API keys and settings at startup before accepting requests.
**Validates: Requirements 8.4**

### Property 8: Metrics recording
*For any* completed request, the system should record metrics including provider, tokens, time, and success/failure status.
**Validates: Requirements 9.1, 9.2, 9.3**

### Property 9: Vibe coding integration
*For any* vibe coding role request, the system should use the LLM manager instead of mock responses.
**Validates: Requirements 10.1**

### Property 10: Error message clarity
*For any* failed generation, the system should return a user-friendly error message without exposing internal details.
**Validates: Requirements 7.4**

## Error Handling

### Error Categories

1. **Provider Errors:**
   - API key invalid
   - Rate limit exceeded
   - Model not available
   - Network timeout

2. **System Errors:**
   - Cache unavailable
   - Configuration invalid
   - All providers exhausted

3. **User Errors:**
   - Invalid prompt
   - Excessive token request

### Error Handling Strategy

```python
try:
    response = await provider.generate(prompt)
except RateLimitError:
    # Immediate switch to next provider
    await manager.switch_provider()
    response = await manager.generate(prompt)
except APIError as e:
    # Retry with exponential backoff
    for attempt in range(3):
        await asyncio.sleep(2 ** attempt)
        try:
            response = await provider.generate(prompt)
            break
        except APIError:
            if attempt == 2:
                # Switch provider after all retries
                await manager.switch_provider()
                response = await manager.generate(prompt)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise SystemError("Generation failed")
```

## Testing Strategy

### Unit Tests

1. **Provider Adapters:**
   - Test API client initialization
   - Test request formatting
   - Test response parsing
   - Test error handling

2. **LLM Manager:**
   - Test provider selection logic
   - Test fallback mechanism
   - Test rate limit checking

3. **Cache Service:**
   - Test cache hit/miss
   - Test TTL expiration
   - Test LRU eviction

### Property-Based Tests

1. **Fallback Chain:**
   - Generate random provider failures
   - Verify system tries all providers

2. **Rate Limiting:**
   - Generate burst of requests
   - Verify limits are enforced

3. **Cache Consistency:**
   - Generate identical requests
   - Verify same results returned

### Integration Tests

1. **End-to-End Generation:**
   - Test complete flow from request to response
   - Test with real API calls (using test keys)

2. **Provider Switching:**
   - Simulate rate limit
   - Verify automatic switch

3. **Vibe Coding Integration:**
   - Test all 6 roles with real LLM
   - Verify formatting for Telegram

## Performance Considerations

### Optimization Strategies

1. **Caching:**
   - 30%+ reduction in API calls
   - Sub-millisecond cache lookups

2. **Parallel Requests:**
   - Batch multiple prompts
   - Use asyncio for concurrency

3. **Provider Selection:**
   - Prefer fastest provider (Groq)
   - Track average response times

4. **Token Optimization:**
   - Trim unnecessary whitespace
   - Use efficient prompts

### Expected Performance

- **Cache Hit:** < 10ms
- **Groq Generation:** 1-2 seconds
- **Gemini Generation:** 2-4 seconds
- **HuggingFace Generation:** 3-6 seconds
- **Fallback Switch:** < 100ms

## Security Considerations

1. **API Key Management:**
   - Store in environment variables
   - Never log API keys
   - Rotate keys periodically

2. **Rate Limit Protection:**
   - Prevent abuse
   - User-level rate limiting

3. **Content Filtering:**
   - Validate prompts
   - Filter inappropriate content

4. **Error Information:**
   - Don't expose internal errors
   - Log detailed errors server-side

## Monitoring and Observability

### Metrics to Track

1. **Request Metrics:**
   - Total requests per provider
   - Success/failure rate
   - Average response time

2. **Rate Limit Metrics:**
   - Current usage vs limit
   - Time until reset
   - Limit exceeded events

3. **Cache Metrics:**
   - Hit rate
   - Miss rate
   - Eviction rate

4. **Cost Metrics:**
   - Tokens used per provider
   - Estimated cost (if applicable)

### Dashboards

1. **Provider Health:**
   - Availability status
   - Response times
   - Error rates

2. **Usage Statistics:**
   - Requests over time
   - Provider distribution
   - Cache effectiveness

3. **Rate Limits:**
   - Current usage
   - Remaining quota
   - Reset timers

## Deployment

### Environment Variables

```bash
# Groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama3-70b-8192

# Gemini
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-pro

# Hugging Face
HF_API_KEY=hf_...
HF_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1

# Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Provider Priority
LLM_PROVIDER_PRIORITY=groq,gemini,huggingface
```

### Docker Configuration

```yaml
services:
  bot:
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - HF_API_KEY=${HF_API_KEY}
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

## Future Enhancements

1. **Additional Providers:**
   - Anthropic Claude (when free tier available)
   - Cohere
   - Local Ollama models

2. **Advanced Caching:**
   - Semantic similarity matching
   - Prompt compression

3. **Load Balancing:**
   - Distribute across providers
   - Optimize for cost/speed

4. **Fine-tuning:**
   - Custom models for specific tasks
   - Domain-specific optimization
