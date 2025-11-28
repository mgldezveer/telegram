"""
Hugging Face LLM Provider - Free inference API with fallback models
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio

try:
    from huggingface_hub import AsyncInferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    AsyncInferenceClient = None

from ..base_provider import (
    BaseLLMProvider,
    APIError,
    RateLimitError,
    AuthenticationError,
    TimeoutError as ProviderTimeoutError
)
from ..models import RateLimitInfo

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseLLMProvider):
    """
    Hugging Face LLM Provider
    
    Features:
    - Free inference API
    - Multiple model fallback
    - Models: Mixtral, Llama, Mistral
    - Can be slower than other providers
    """
    
    # Rate limits (conservative estimates for free tier)
    REQUESTS_PER_MINUTE = 30
    REQUESTS_PER_DAY = 1000
    
    # Default models in priority order
    DEFAULT_MODELS = [
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "meta-llama/Llama-2-70b-chat-hf",
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        fallback_models: Optional[List[str]] = None
    ):
        """
        Initialize Hugging Face provider.
        
        Args:
            api_key: HF API token (optional, but recommended)
            model: Primary model name
            fallback_models: List of fallback models if primary fails
        """
        if not HF_AVAILABLE:
            raise ImportError(
                "Hugging Face Hub not installed. "
                "Install with: pip install huggingface-hub"
            )
        
        super().__init__(api_key or "", model)
        
        # Initialize client
        self.client = AsyncInferenceClient(token=api_key)
        
        # Setup fallback models
        self.fallback_models = fallback_models or self.DEFAULT_MODELS.copy()
        if model not in self.fallback_models:
            self.fallback_models.insert(0, model)
        
        # Rate limiting
        self.request_count = 0
        self.daily_count = 0
        self.last_reset = datetime.utcnow()
        self.last_daily_reset = datetime.utcnow()
        
        # Track model availability
        self.unavailable_models = set()
        self.last_availability_check = {}
        
        logger.info(f"✅ HuggingFace provider initialized with model: {model}")
        logger.info(f"   Fallback models: {', '.join(self.fallback_models[1:])}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using Hugging Face API with fallback.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 1.0)
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
            
        Raises:
            APIError: If all models fail
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If API key is invalid
            ProviderTimeoutError: If request times out
        """
        # Check rate limits
        if self._is_rate_limited():
            raise RateLimitError(
                f"HuggingFace rate limit exceeded. Resets at {self.last_reset + timedelta(minutes=1)}"
            )
        
        if self._is_daily_limit_reached():
            raise RateLimitError(
                f"HuggingFace daily limit reached. Resets at {self.last_daily_reset + timedelta(days=1)}"
            )
        
        # Prepare full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
        else:
            full_prompt = f"<s>[INST] {prompt} [/INST]"
        
        # Try each model in fallback chain
        last_error = None
        for model_name in self._get_available_models():
            try:
                logger.debug(f"Trying HuggingFace model: {model_name}")
                
                # Make async request with timeout
                response = await asyncio.wait_for(
                    self._make_request(model_name, full_prompt, max_tokens, temperature),
                    timeout=60.0  # HF can be slower
                )
                
                # Extract text
                text = response.strip()
                
                # Update rate limit counters
                self.request_count += 1
                self.daily_count += 1
                
                logger.info(f"✅ HuggingFace generation successful with {model_name} ({len(text)} chars)")
                return text
                
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ HuggingFace model {model_name} timed out")
                self._mark_model_unavailable(model_name, duration_minutes=5)
                last_error = ProviderTimeoutError(f"Model {model_name} timed out")
                continue
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for specific error types
                if "rate limit" in error_msg or "429" in error_msg:
                    logger.warning("⚠️ HuggingFace rate limit hit")
                    raise RateLimitError(f"HuggingFace rate limit exceeded: {e}")
                
                elif "unauthorized" in error_msg or "401" in error_msg or "403" in error_msg:
                    logger.error("❌ HuggingFace authentication failed")
                    raise AuthenticationError(f"Invalid HuggingFace API key: {e}")
                
                elif "model" in error_msg and ("not found" in error_msg or "unavailable" in error_msg):
                    logger.warning(f"⚠️ HuggingFace model {model_name} unavailable: {e}")
                    self._mark_model_unavailable(model_name, duration_minutes=10)
                    last_error = APIError(f"Model {model_name} unavailable: {e}")
                    continue
                
                else:
                    logger.warning(f"⚠️ HuggingFace error with {model_name}: {e}")
                    last_error = APIError(f"HuggingFace error: {e}")
                    continue
        
        # All models failed
        logger.error("❌ All HuggingFace models failed")
        if last_error:
            raise last_error
        else:
            raise APIError("All HuggingFace models failed")
    
    async def _make_request(self, model_name, prompt, max_tokens, temperature):
        """Make async request to Hugging Face API"""
        return await self.client.text_generation(
            prompt,
            model=model_name,
            max_new_tokens=max_tokens,
            temperature=temperature,
            return_full_text=False
        )
    
    def _get_available_models(self) -> List[str]:
        """Get list of currently available models"""
        now = datetime.utcnow()
        available = []
        
        for model in self.fallback_models:
            # Check if model is marked unavailable
            if model in self.unavailable_models:
                # Check if cooldown period has passed
                last_check = self.last_availability_check.get(model)
                if last_check and (now - last_check).total_seconds() < 300:  # 5 min cooldown
                    continue
                else:
                    # Remove from unavailable set to retry
                    self.unavailable_models.discard(model)
            
            available.append(model)
        
        return available if available else self.fallback_models
    
    def _mark_model_unavailable(self, model_name: str, duration_minutes: int = 5):
        """Mark a model as temporarily unavailable"""
        self.unavailable_models.add(model_name)
        self.last_availability_check[model_name] = datetime.utcnow()
        logger.info(f"Marked {model_name} as unavailable for {duration_minutes} minutes")
    
    async def check_availability(self) -> bool:
        """
        Check if Hugging Face API is available.
        
        Returns:
            True if at least one model is available, False otherwise
        """
        for model_name in self.fallback_models[:2]:  # Check first 2 models
            try:
                # Try a minimal request
                response = await asyncio.wait_for(
                    self._make_request(
                        model_name,
                        "<s>[INST] Hi [/INST]",
                        max_tokens=5,
                        temperature=0.1
                    ),
                    timeout=15.0
                )
                
                logger.info(f"✅ HuggingFace API is available (model: {model_name})")
                return True
                
            except Exception as e:
                logger.debug(f"Model {model_name} check failed: {e}")
                continue
        
        logger.warning("⚠️ HuggingFace API unavailable (all models failed)")
        return False
    
    def get_rate_limit_info(self) -> RateLimitInfo:
        """
        Get rate limit information.
        
        Returns:
            RateLimitInfo with current limits
        """
        # Reset minute counter if minute has passed
        if datetime.utcnow() - self.last_reset > timedelta(minutes=1):
            self.request_count = 0
            self.last_reset = datetime.utcnow()
        
        # Reset daily counter if day has passed
        if datetime.utcnow() - self.last_daily_reset > timedelta(days=1):
            self.daily_count = 0
            self.last_daily_reset = datetime.utcnow()
        
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
        """Check if currently rate limited (per minute)"""
        # Reset if minute passed
        if datetime.utcnow() - self.last_reset > timedelta(minutes=1):
            self.request_count = 0
            self.last_reset = datetime.utcnow()
            return False
        
        return self.request_count >= self.REQUESTS_PER_MINUTE
    
    def _is_daily_limit_reached(self) -> bool:
        """Check if daily limit is reached"""
        # Reset if day passed
        if datetime.utcnow() - self.last_daily_reset > timedelta(days=1):
            self.daily_count = 0
            self.last_daily_reset = datetime.utcnow()
            return False
        
        return self.daily_count >= self.REQUESTS_PER_DAY
    
    def __str__(self) -> str:
        available_count = len(self._get_available_models())
        return f"HuggingFaceProvider(model={self.model}, available_models={available_count}/{len(self.fallback_models)}, remaining={self.get_remaining_quota()})"


# Convenience function to create HuggingFace provider from environment
def create_huggingface_provider_from_env() -> Optional[HuggingFaceProvider]:
    """
    Create HuggingFace provider from environment variables.
    
    Returns:
        HuggingFaceProvider instance or None if disabled
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("HUGGINGFACE_API_KEY")  # Optional
    model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")
    enabled = os.getenv("LLM_HUGGINGFACE_ENABLED", "true").lower() == "true"
    
    if not enabled:
        logger.warning("⚠️ HuggingFace provider disabled")
        return None
    
    try:
        provider = HuggingFaceProvider(api_key=api_key, model=model)
        logger.info("✅ HuggingFace provider created from environment")
        return provider
    except Exception as e:
        logger.error(f"❌ Failed to create HuggingFace provider: {e}")
        return None
