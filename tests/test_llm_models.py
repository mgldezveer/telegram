"""
Unit tests for LLM models
"""

import pytest
from datetime import datetime, timedelta
from src.llm.models import LLMResponse, ProviderStatus, RateLimitInfo, UsageStats


class TestLLMResponse:
    """Tests for LLMResponse model"""
    
    def test_create_response(self):
        """Test creating LLMResponse"""
        response = LLMResponse(
            text="Generated text",
            provider="groq",
            model="llama3-70b",
            tokens_used=100,
            generation_time=1.5
        )
        
        assert response.text == "Generated text"
        assert response.provider == "groq"
        assert response.model == "llama3-70b"
        assert response.tokens_used == 100
        assert response.generation_time == 1.5
        assert response.cached is False
        assert isinstance(response.timestamp, datetime)
    
    def test_cached_response(self):
        """Test cached response"""
        response = LLMResponse(
            text="Cached text",
            provider="groq",
            model="llama3-70b",
            tokens_used=50,
            generation_time=0.01,
            cached=True
        )
        
        assert response.cached is True
        assert "cached" in str(response).lower()
    
    def test_response_with_metadata(self):
        """Test response with metadata"""
        metadata = {"temperature": 0.7, "max_tokens": 1000}
        response = LLMResponse(
            text="Text",
            provider="gemini",
            model="gemini-pro",
            tokens_used=75,
            generation_time=2.0,
            metadata=metadata
        )
        
        assert response.metadata == metadata
        assert response.metadata["temperature"] == 0.7


class TestProviderStatus:
    """Tests for ProviderStatus model"""
    
    def test_create_status(self):
        """Test creating ProviderStatus"""
        reset_time = datetime.utcnow() + timedelta(minutes=1)
        status = ProviderStatus(
            name="groq",
            available=True,
            rate_limit_remaining=25,
            rate_limit_reset_at=reset_time
        )
        
        assert status.name == "groq"
        assert status.available is True
        assert status.rate_limit_remaining == 25
        assert status.rate_limit_reset_at == reset_time
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        status = ProviderStatus(
            name="groq",
            available=True,
            rate_limit_remaining=30,
            rate_limit_reset_at=datetime.utcnow(),
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )
        
        assert status.success_rate == 95.0
        assert status.error_rate == 5.0
    
    def test_zero_requests(self):
        """Test with zero requests"""
        status = ProviderStatus(
            name="groq",
            available=True,
            rate_limit_remaining=30,
            rate_limit_reset_at=datetime.utcnow()
        )
        
        assert status.success_rate == 0.0
        assert status.error_rate == 0.0
    
    def test_unavailable_status(self):
        """Test unavailable provider"""
        status = ProviderStatus(
            name="groq",
            available=False,
            rate_limit_remaining=0,
            rate_limit_reset_at=datetime.utcnow(),
            last_error="API key invalid"
        )
        
        assert status.available is False
        assert status.last_error == "API key invalid"
        assert "❌" in str(status) or "Unavailable" in str(status)


class TestRateLimitInfo:
    """Tests for RateLimitInfo model"""
    
    def test_create_rate_limit(self):
        """Test creating RateLimitInfo"""
        rate_limit = RateLimitInfo(
            requests_per_minute=30,
            requests_per_hour=1800,
            current_usage=10
        )
        
        assert rate_limit.requests_per_minute == 30
        assert rate_limit.requests_per_hour == 1800
        assert rate_limit.current_usage == 10
    
    def test_limit_not_reached(self):
        """Test when limit is not reached"""
        rate_limit = RateLimitInfo(
            requests_per_minute=30,
            current_usage=10
        )
        
        assert rate_limit.is_limit_reached() is False
        assert rate_limit.get_remaining() == 20
    
    def test_limit_reached(self):
        """Test when limit is reached"""
        rate_limit = RateLimitInfo(
            requests_per_minute=30,
            current_usage=30
        )
        
        assert rate_limit.is_limit_reached() is True
        assert rate_limit.get_remaining() == 0
    
    def test_limit_exceeded(self):
        """Test when limit is exceeded"""
        rate_limit = RateLimitInfo(
            requests_per_minute=30,
            current_usage=35
        )
        
        assert rate_limit.is_limit_reached() is True
        assert rate_limit.get_remaining() < 0
    
    def test_multiple_limits(self):
        """Test with multiple limit types"""
        rate_limit = RateLimitInfo(
            requests_per_minute=30,
            requests_per_hour=1000,
            requests_per_day=10000,
            current_usage=25
        )
        
        # Should use the most restrictive limit (per minute)
        assert rate_limit.get_remaining() == 5
    
    def test_no_limits(self):
        """Test with no limits set"""
        rate_limit = RateLimitInfo(current_usage=100)
        
        assert rate_limit.is_limit_reached() is False
        assert rate_limit.get_remaining() == float('inf')


class TestUsageStats:
    """Tests for UsageStats model"""
    
    def test_create_usage_stats(self):
        """Test creating UsageStats"""
        stats = UsageStats(provider="groq")
        
        assert stats.provider == "groq"
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
    
    def test_success_rate(self):
        """Test success rate calculation"""
        stats = UsageStats(
            provider="groq",
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )
        
        assert stats.success_rate == 95.0
    
    def test_cache_hit_rate(self):
        """Test cache hit rate calculation"""
        stats = UsageStats(
            provider="groq",
            cache_hits=30,
            cache_misses=70
        )
        
        assert stats.cache_hit_rate == 30.0
    
    def test_update_response_time(self):
        """Test updating response time"""
        stats = UsageStats(
            provider="groq",
            successful_requests=2
        )
        
        stats.update_response_time(1.0)
        stats.update_response_time(3.0)
        
        assert stats.total_response_time == 4.0
        assert stats.avg_response_time == 2.0
    
    def test_zero_requests_stats(self):
        """Test with zero requests"""
        stats = UsageStats(provider="groq")
        
        assert stats.success_rate == 0.0
        assert stats.cache_hit_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
