"""
Base abstract class for LLM providers
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

from .models import RateLimitInfo, ProviderStatus

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    All provider implementations must inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize provider with API key and model name.
        
        Args:
            api_key: API key for the provider
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()
        logger.info(f"Initializing {self.provider_name} provider with model {model}")
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text from prompt.
        
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
        """
        pass
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """
        Check if provider is available and API key is valid.
        
        Returns:
            True if provider is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_rate_limit_info(self) -> RateLimitInfo:
        """
        Get rate limit information for this provider.
        
        Returns:
            RateLimitInfo object with current limits
        """
        pass
    
    @abstractmethod
    def get_remaining_quota(self) -> int:
        """
        Get remaining quota for this provider.
        
        Returns:
            Number of remaining requests before rate limit
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        return self.provider_name
    
    def get_model_name(self) -> str:
        """Get the model name being used"""
        return self.model
    
    async def get_status(self) -> ProviderStatus:
        """
        Get current status of this provider.
        
        Returns:
            ProviderStatus object with current state
        """
        from datetime import datetime
        
        available = await self.check_availability()
        rate_limit_info = self.get_rate_limit_info()
        
        return ProviderStatus(
            name=self.provider_name,
            available=available,
            rate_limit_remaining=rate_limit_info.get_remaining(),
            rate_limit_reset_at=rate_limit_info.reset_at,
            last_error=None,
            avg_response_time=0.0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0
        )
    
    def __str__(self) -> str:
        return f"{self.provider_name.capitalize()}Provider(model={self.model})"
    
    def __repr__(self) -> str:
        return self.__str__()


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class APIError(ProviderError):
    """Raised when API request fails"""
    pass


class RateLimitError(ProviderError):
    """Raised when rate limit is exceeded"""
    pass


class AuthenticationError(ProviderError):
    """Raised when API key is invalid"""
    pass


class ModelNotAvailableError(ProviderError):
    """Raised when requested model is not available"""
    pass


class TimeoutError(ProviderError):
    """Raised when request times out"""
    pass
