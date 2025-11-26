"""
Groq LLM Provider - Fast inference with Llama 3 and Mixtral
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
import asyncio

try:
    from groq import Groq, AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None
    AsyncGroq = None

from ..base_provider import (
    BaseLLMProvider,
    APIError,
    RateLimitError,
    AuthenticationError,
    TimeoutError as ProviderTimeoutError
)
from ..models import RateLimitInfo

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """
    Groq LLM Provider
    
    Features:
    - Very fast inference (< 1 second)
    - Free tier: 30 requests per minute
    - Models: Llama 3 70B, Mixtral 8x7B
    """
    
    # Rate limits for free tier
    REQUESTS_PER_MINUTE = 30
    REQUESTS_PER_DAY = 14400  # 30 * 60 * 8 (assuming 8 hours usage)
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq provider.
        
        Args:
            api_key: Groq API key
            model: Model name (default: llama3-70b-8192)
        """
        if not GROQ_AVAILABLE:
            raise ImportError(
                "Groq SDK not installed. Install with: pip install groq"
            )
        
        super().__init__(api_key, model)
        
        # Initialize clients
        self.client = Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)
        
        # Rate limiting
        self.request_count = 0
        self.last_reset = datetime.utcnow()
        
        logger.info(f"✅ Groq provider initialized with model: {model}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using Groq API.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 1.0)
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
            
        Raises:
            APIError: If API request fails
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If API key is invalid
            ProviderTimeoutError: If request times out
        """
        # Check rate limit
        if self._is_rate_limited():
            raise RateLimitError(
                f"Groq rate limit exceeded. Resets at {self.last_reset + timedelta(minutes=1)}"
            )
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            logger.debug(f"Sending request to Groq with model {self.model}")
            
            # Make async request
            response = await asyncio.wait_for(
                self._make_request(messages, max_tokens, temperature),
                timeout=30.0
            )
            
            # Extract text
            text = response.choices[0].message.content
            
            # Update rate limit counter
            self.request_count += 1
            
            logger.info(f"✅ Groq generation successful ({len(text)} chars)")
            return text
            
        except asyncio.TimeoutError:
            logger.error("❌ Groq request timed out")
            raise ProviderTimeoutError("Groq request timed out after 30 seconds")
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for specific error types
            if "rate limit" in error_msg or "429" in error_msg:
                logger.warning("⚠️ Groq rate limit hit")
                raise RateLimitError(f"Groq rate limit exceeded: {e}")
            
            elif "unauthorized" in error_msg or "401" in error_msg or "invalid" in error_msg:
                logger.error("❌ Groq authentication failed")
                raise AuthenticationError(f"Invalid Groq API key: {e}")
            
            else:
                logger.error(f"❌ Groq API error: {e}")
                raise APIError(f"Groq API error: {e}")
    
    async def _make_request(self, messages, max_tokens, temperature):
        """Make async request to Groq API"""
        return await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False
        )
    
    async def check_availability(self) -> bool:
        """
        Check if Groq API is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            # Try a minimal request
            test_messages = [{"role": "user", "content": "Hi"}]
            response = await asyncio.wait_for(
                self._make_request(test_messages, max_tokens=5, temperature=0.1),
                timeout=10.0
            )
            
            logger.info("✅ Groq API is available")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Groq API unavailable: {e}")
            return False
    
    def get_rate_limit_info(self) -> RateLimitInfo:
        """
        Get rate limit information.
        
        Returns:
            RateLimitInfo with current limits
        """
        # Reset counter if minute has passed
        if datetime.utcnow() - self.last_reset > timedelta(minutes=1):
            self.request_count = 0
            self.last_reset = datetime.utcnow()
        
        return RateLimitInfo(
            requests_per_minute=self.REQUESTS_PER_MINUTE,
            requests_per_day=self.REQUESTS_PER_DAY,
            current_usage=self.request_count,
            reset_at=self.last_reset + timedelta(minutes=1)
        )
    
    def get_remaining_quota(self) -> int:
        """
        Get remaining requests before rate limit.
        
        Returns:
            Number of remaining requests
        """
        rate_limit = self.get_rate_limit_info()
        return rate_limit.get_remaining()
    
    def _is_rate_limited(self) -> bool:
        """Check if currently rate limited"""
        # Reset if minute passed
        if datetime.utcnow() - self.last_reset > timedelta(minutes=1):
            self.request_count = 0
            self.last_reset = datetime.utcnow()
            return False
        
        return self.request_count >= self.REQUESTS_PER_MINUTE
    
    def __str__(self) -> str:
        return f"GroqProvider(model={self.model}, remaining={self.get_remaining_quota()})"


# Convenience function to create Groq provider from environment
def create_groq_provider_from_env() -> Optional[GroqProvider]:
    """
    Create Groq provider from environment variables.
    
    Returns:
        GroqProvider instance or None if not configured
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    enabled = os.getenv("LLM_GROQ_ENABLED", "true").lower() == "true"
    
    if not api_key or not enabled:
        logger.warning("⚠️ Groq provider not configured or disabled")
        return None
    
    try:
        provider = GroqProvider(api_key=api_key, model=model)
        logger.info("✅ Groq provider created from environment")
        return provider
    except Exception as e:
        logger.error(f"❌ Failed to create Groq provider: {e}")
        return None
