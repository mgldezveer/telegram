"""
LLM Integration Module

Provides integration with multiple free LLM providers:
- Groq (fastest)
- Google Gemini (quality)
- Hugging Face (open models)
"""

from .models import LLMResponse, ProviderStatus, RateLimitInfo, UsageStats
from .base_provider import BaseLLMProvider, ProviderError, APIError, RateLimitError, AuthenticationError, ModelNotAvailableError, TimeoutError
from .llm_manager import LLMManager, create_llm_manager_from_env
from .rate_limit_manager import RateLimitManager, create_rate_limit_manager_from_env
from .cache_service import CacheService, create_cache_service_from_env
from .providers import (
    GroqProvider,
    GeminiProvider,
    HuggingFaceProvider,
    create_groq_provider_from_env,
    create_gemini_provider_from_env,
    create_huggingface_provider_from_env
)

__all__ = [
    # Models
    'LLMResponse',
    'ProviderStatus',
    'RateLimitInfo',
    'UsageStats',
    # Base
    'BaseLLMProvider',
    'ProviderError',
    'APIError',
    'RateLimitError',
    'AuthenticationError',
    'ModelNotAvailableError',
    'TimeoutError',
    # Manager
    'LLMManager',
    'create_llm_manager_from_env',
    # Services
    'RateLimitManager',
    'create_rate_limit_manager_from_env',
    'CacheService',
    'create_cache_service_from_env',
    # Providers
    'GroqProvider',
    'GeminiProvider',
    'HuggingFaceProvider',
    'create_groq_provider_from_env',
    'create_gemini_provider_from_env',
    'create_huggingface_provider_from_env',
]