"""
Data models for LLM integration
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class LLMResponse:
    """Response from LLM generation"""
    text: str
    provider: str
    model: str
    tokens_used: int
    generation_time: float
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __str__(self) -> str:
        cache_status = "cached" if self.cached else "generated"
        return (
            f"LLMResponse({cache_status}, provider={self.provider}, "
            f"model={self.model}, tokens={self.tokens_used}, "
            f"time={self.generation_time:.2f}s)"
        )


@dataclass
class ProviderStatus:
    """Status of an LLM provider"""
    name: str
    available: bool
    rate_limit_remaining: int
    rate_limit_reset_at: datetime
    last_error: Optional[str] = None
    avg_response_time: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100
    
    def __str__(self) -> str:
        status = "✅ Available" if self.available else "❌ Unavailable"
        return (
            f"{self.name}: {status}\n"
            f"  Rate Limit: {self.rate_limit_remaining} remaining\n"
            f"  Avg Response: {self.avg_response_time:.2f}s\n"
            f"  Success Rate: {self.success_rate:.1f}%"
        )


@dataclass
class RateLimitInfo:
    """Rate limit information for a provider"""
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    current_usage: int = 0
    reset_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_limit_reached(self) -> bool:
        """Check if any rate limit is reached"""
        if self.requests_per_minute and self.current_usage >= self.requests_per_minute:
            return True
        if self.requests_per_hour and self.current_usage >= self.requests_per_hour:
            return True
        if self.requests_per_day and self.current_usage >= self.requests_per_day:
            return True
        return False
    
    def get_remaining(self) -> int:
        """Get remaining requests before limit"""
        limits = [
            self.requests_per_minute,
            self.requests_per_hour,
            self.requests_per_day
        ]
        active_limits = [l for l in limits if l is not None]
        if not active_limits:
            return float('inf')
        return min(active_limits) - self.current_usage
    
    def __str__(self) -> str:
        parts = []
        if self.requests_per_minute:
            parts.append(f"{self.requests_per_minute}/min")
        if self.requests_per_hour:
            parts.append(f"{self.requests_per_hour}/hour")
        if self.requests_per_day:
            parts.append(f"{self.requests_per_day}/day")
        
        limit_str = ", ".join(parts) if parts else "No limits"
        return f"RateLimit({limit_str}, current={self.current_usage}, remaining={self.get_remaining()})"


@dataclass
class UsageStats:
    """Usage statistics for a provider"""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    total_response_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def cache_hit_rate(self) -> float:
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100
    
    def update_response_time(self, response_time: float):
        """Update average response time"""
        self.total_response_time += response_time
        if self.successful_requests > 0:
            self.avg_response_time = self.total_response_time / self.successful_requests
    
    def __str__(self) -> str:
        return (
            f"UsageStats({self.provider}):\n"
            f"  Requests: {self.total_requests} (✅ {self.successful_requests}, ❌ {self.failed_requests})\n"
            f"  Success Rate: {self.success_rate:.1f}%\n"
            f"  Tokens Used: {self.total_tokens}\n"
            f"  Cache Hit Rate: {self.cache_hit_rate:.1f}%\n"
            f"  Avg Response Time: {self.avg_response_time:.2f}s"
        )
