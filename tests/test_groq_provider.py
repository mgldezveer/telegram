"""
Tests for Groq Provider

Note: These tests require a valid GROQ_API_KEY in .env file
"""

import pytest
import asyncio
import os
from dotenv import load_dotenv

from src.llm.providers.groq_provider import GroqProvider, create_groq_provider_from_env
from src.llm.base_provider import RateLimitError, AuthenticationError

# Load environment variables
load_dotenv()

# Skip tests if no API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
skip_if_no_key = pytest.mark.skipif(
    not GROQ_API_KEY,
    reason="GROQ_API_KEY not set in environment"
)


class TestGroqProvider:
    """Tests for Groq Provider"""
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_create_provider(self):
        """Test creating Groq provider"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        assert provider is not None
        assert provider.get_provider_name() == "groq"
        assert provider.get_model_name() == "llama-3.3-70b-versatile"
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_generate_simple(self):
        """Test simple text generation"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        prompt = "Say 'Hello, World!' and nothing else."
        result = await provider.generate(
            prompt=prompt,
            max_tokens=50,
            temperature=0.1
        )
        
        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)
        print(f"\n✅ Generated: {result}")
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test generation with system prompt"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        system_prompt = "You are a helpful assistant that responds in one sentence."
        prompt = "What is 2+2?"
        
        result = await provider.generate(
            prompt=prompt,
            max_tokens=100,
            temperature=0.3,
            system_prompt=system_prompt
        )
        
        assert result is not None
        assert len(result) > 0
        print(f"\n✅ Generated with system prompt: {result}")
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_check_availability(self):
        """Test checking API availability"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        available = await provider.check_availability()
        assert available is True
        print("\n✅ Groq API is available")
    
    @skip_if_no_key
    def test_rate_limit_info(self):
        """Test getting rate limit information"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        rate_limit = provider.get_rate_limit_info()
        
        assert rate_limit is not None
        assert rate_limit.requests_per_minute == 30
        assert rate_limit.current_usage >= 0
        assert rate_limit.get_remaining() <= 30
        
        print(f"\n✅ Rate limit info: {rate_limit}")
    
    @skip_if_no_key
    def test_remaining_quota(self):
        """Test getting remaining quota"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        remaining = provider.get_remaining_quota()
        
        assert remaining >= 0
        assert remaining <= 30
        
        print(f"\n✅ Remaining quota: {remaining}")
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting provider status"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        status = await provider.get_status()
        
        assert status is not None
        assert status.name == "groq"
        assert status.available is True
        assert status.rate_limit_remaining >= 0
        
        print(f"\n✅ Provider status:\n{status}")
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """Test with invalid API key"""
        provider = GroqProvider(
            api_key="invalid_key_12345",
            model="llama-3.3-70b-versatile"
        )
        
        with pytest.raises(AuthenticationError):
            await provider.generate(
                prompt="Test",
                max_tokens=10
            )
        
        print("\n✅ Invalid API key correctly raises AuthenticationError")
    
    @skip_if_no_key
    def test_create_from_env(self):
        """Test creating provider from environment"""
        provider = create_groq_provider_from_env()
        
        assert provider is not None
        assert provider.get_provider_name() == "groq"
        
        print(f"\n✅ Created from env: {provider}")
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_multiple_generations(self):
        """Test multiple generations in sequence"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        prompts = [
            "Count to 3",
            "Say hello",
            "What is AI?"
        ]
        
        results = []
        for prompt in prompts:
            result = await provider.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.5
            )
            results.append(result)
            await asyncio.sleep(0.5)  # Small delay between requests
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result is not None
            assert len(result) > 0
            print(f"\n✅ Generation {i+1}: {result[:100]}...")


class TestGroqProviderIntegration:
    """Integration tests for Groq Provider"""
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_vibe_coding_style_generation(self):
        """Test generation in vibe coding style"""
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        system_prompt = """You are the 'Main Brain' role in vibe coding. 
        Provide a high-level vision for the given topic in 2-3 sentences."""
        
        prompt = "Topic: Creating a Telegram bot"
        
        result = await provider.generate(
            prompt=prompt,
            max_tokens=200,
            temperature=0.7,
            system_prompt=system_prompt
        )
        
        assert result is not None
        assert len(result) > 50  # Should be substantial
        
        print(f"\n✅ Vibe coding generation:\n{result}")
    
    @skip_if_no_key
    @pytest.mark.asyncio
    async def test_fast_response_time(self):
        """Test that Groq is indeed fast (< 3 seconds)"""
        import time
        
        provider = GroqProvider(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile"
        )
        
        start_time = time.time()
        
        result = await provider.generate(
            prompt="Say hello in one word",
            max_tokens=10,
            temperature=0.1
        )
        
        elapsed = time.time() - start_time
        
        assert result is not None
        assert elapsed < 3.0  # Should be very fast
        
        print(f"\n✅ Response time: {elapsed:.2f}s (< 3s)")
        print(f"   Result: {result}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
