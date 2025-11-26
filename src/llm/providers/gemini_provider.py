"""
Google Gemini LLM Provider - High quality generation
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
import asyncio

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from ..base_provider import (
    BaseLLMProvider,
    APIError,
    RateLimitError,
    AuthenticationError,
    TimeoutError as ProviderTimeoutError
)
from ..models import RateLimitInfo

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM Provider
    
    Features:
    - High quality generation
    - Free tier: 60 requests per minute
    - Model: gemini-pro
    - Built-in safety settings
    """
    
    # Rate limits for free tier
    REQUESTS_PER_MINUTE = 60
    REQUESTS_PER_DAY = 1500
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            model: Model name (default: gemini-pro)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "Google Generative AI SDK not installed. Install with: pip install google-generativeai"
            )
        
        super().__init__(api_key, model)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.client = genai.GenerativeModel(model)
        
        # Rate limiting
        self.request_count = 0
        self.last_reset = datetime.utcnow()
        
        logger.info(f"✅ Gemini provider initialized with model: {model}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using Gemini API.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 1.0)
            system_prompt: Optional system prompt (prepended to prompt)
            
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
                f"Gemini rate limit exceeded. Resets at {self.last_reset + timedelta(minutes=1)}"
            )
        
        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            logger.debug(f"Sending request to Gemini with model {self.model}")
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Make async request
            response = await asyncio.wait_for(
                self._make_request(full_prompt, generation_config),
                timeout=30.0
            )
            
            # Extract text
            text = response.text
            
            # Update rate limit counter
            self.request_count += 1
            
            logger.info(f"✅ Gemini generation successful ({len(text)} chars)")
            return text
            
        except asyncio.TimeoutError:
            logger.error("❌ Gemini request timed out")
            raise ProviderTimeoutError("Gemini request timed out after 30 seconds")
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for specific error types
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                logger.warning("⚠️ Gemini rate limit hit")
                raise RateLimitError(f"Gemini rate limit exceeded: {e}")
            
            elif "api key" in error_msg or "401" in error_msg or "403" in error_msg:
                logger.error("❌ Gemini authentication failed")
                raise AuthenticationError(f"Invalid Gemini API key: {e}")
            
            else:
                logger.error(f"❌ Gemini API error: {e}")
                raise APIError(f"Gemini API error: {e}")
    
    async def _make_request(self, prompt, generation_config):
        """Make async request to Gemini API"""
        # Gemini SDK doesn't have native async, so we run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
        )
    
    async def check_availability(self) -> bool:
        """
        Check if Gemini API is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            # Try a minimal request
            response = await asyncio.wait_for(
                self._make_request(
                    "Hi",
                    genai.types.GenerationConfig(max_output_tokens=5)
                ),
                timeout=10.0
            )
            
            logger.info("✅ Gemini API is available")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Gemini API unavailable: {e}")
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
        return f"GeminiProvider(model={self.model}, remaining={self.get_remaining_quota()})"


# Convenience function to create Gemini provider from environment
def create_gemini_provider_from_env() -> Optional[GeminiProvider]:
    """
    Create Gemini provider from environment variables.
    
    Returns:
        GeminiProvider instance or None if not configured
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-pro")
    enabled = os.getenv("LLM_GEMINI_ENABLED", "false").lower() == "true"
    
    if not api_key or not enabled:
        logger.warning("⚠️ Gemini provider not configured or disabled")
        return None
    
    try:
        provider = GeminiProvider(api_key=api_key, model=model)
        logger.info("✅ Gemini provider created from environment")
        return provider
    except Exception as e:
        logger.error(f"❌ Failed to create Gemini provider: {e}")
        return None
