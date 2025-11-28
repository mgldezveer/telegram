"""
LLM Manager - Orchestrates multiple LLM providers with fallback, caching, and rate limiting
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from .base_provider import (
    BaseLLMProvider,
    APIError,
    RateLimitError,
    AuthenticationError,
    TimeoutError as ProviderTimeoutError
)
from .providers import (
    GroqProvider,
    GeminiProvider,
    HuggingFaceProvider,
    create_groq_provider_from_env,
    create_gemini_provider_from_env,
    create_huggingface_provider_from_env
)
from .rate_limit_manager import RateLimitManager, create_rate_limit_manager_from_env
from .cache_service import CacheService, create_cache_service_from_env

logger = logging.getLogger(__name__)


class LLMManager:
    """
    LLM Manager - Central orchestrator for all LLM operations.
    
    Features:
    - Multiple provider support with automatic fallback
    - Intelligent provider selection based on availability
    - Rate limit management across all providers
    - Response caching to reduce API calls
    - Retry logic with exponential backoff
    - Comprehensive statistics and monitoring
    """
    
    def __init__(
        self,
        providers: Optional[List[BaseLLMProvider]] = None,
        rate_limit_manager: Optional[RateLimitManager] = None,
        cache_service: Optional[CacheService] = None,
        enable_cache: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize LLM Manager.
        
        Args:
            providers: List of LLM providers (in priority order)
            rate_limit_manager: Rate limit manager instance
            cache_service: Cache service instance
            enable_cache: Whether to use caching
            max_retries: Maximum retry attempts per provider
        """
        self.providers = providers or []
        self.rate_limit_manager = rate_limit_manager
        self.cache_service = cache_service
        self.enable_cache = enable_cache and cache_service is not None
        self.max_retries = max_retries
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'provider_usage': {},
            'errors': {},
            'last_request': None
        }
        
        logger.info(f"✅ LLM Manager initialized with {len(self.providers)} providers")
        logger.info(f"   Cache: {'Enabled' if self.enable_cache else 'Disabled'}")
        logger.info(f"   Rate limiting: {'Enabled' if self.rate_limit_manager else 'Disabled'}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None
    ) -> str:
        """
        Generate text using available LLM providers.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 1.0)
            system_prompt: Optional system prompt
            preferred_provider: Optional preferred provider name
            
        Returns:
            Generated text
            
        Raises:
            APIError: If all providers fail
        """
        self.stats['total_requests'] += 1
        self.stats['last_request'] = datetime.utcnow().isoformat()
        
        # Check cache first
        if self.enable_cache:
            cached_response = await self._check_cache(
                prompt, max_tokens, temperature, system_prompt
            )
            if cached_response:
                self.stats['cache_hits'] += 1
                logger.info("✅ Returning cached response")
                return cached_response
            else:
                self.stats['cache_misses'] += 1
        
        # Get provider order (preferred first if specified)
        provider_order = self._get_provider_order(preferred_provider)
        
        if not provider_order:
            raise APIError("No LLM providers available")
        
        # Try each provider with fallback
        last_error = None
        for provider in provider_order:
            provider_name = provider.__class__.__name__.replace('Provider', '').lower()
            
            try:
                # Check rate limit
                if self.rate_limit_manager:
                    if not await self._check_rate_limit(provider_name):
                        logger.warning(f"⚠️ {provider_name} rate limited, trying next provider")
                        continue
                
                # Generate with retry
                response = await self._generate_with_retry(
                    provider,
                    prompt,
                    max_tokens,
                    temperature,
                    system_prompt
                )
                
                # Record request
                if self.rate_limit_manager:
                    await self.rate_limit_manager.record_request(provider_name)
                
                # Cache response
                if self.enable_cache:
                    await self._cache_response(
                        prompt, max_tokens, temperature, system_prompt, response, provider
                    )
                
                # Update statistics
                self._update_provider_stats(provider_name, success=True)
                
                logger.info(f"✅ Successfully generated with {provider_name}")
                return response
                
            except RateLimitError as e:
                logger.warning(f"⚠️ {provider_name} rate limit: {e}")
                last_error = e
                continue
                
            except (APIError, ProviderTimeoutError, AuthenticationError) as e:
                logger.warning(f"⚠️ {provider_name} failed: {e}")
                self._update_provider_stats(provider_name, success=False, error=str(e))
                last_error = e
                continue
        
        # All providers failed
        logger.error("❌ All LLM providers failed")
        if last_error:
            raise last_error
        else:
            raise APIError("All LLM providers failed")
    
    async def _generate_with_retry(
        self,
        provider: BaseLLMProvider,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Generate with exponential backoff retry"""
        for attempt in range(self.max_retries):
            try:
                return await provider.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt
                )
            except (APIError, ProviderTimeoutError) as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.debug(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise
    
    async def _check_cache(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> Optional[str]:
        """Check cache for response"""
        if not self.cache_service:
            return None
        
        # Use first provider's model for cache key (they should be similar)
        model = self.providers[0].model if self.providers else "unknown"
        
        cache_key = self.cache_service.generate_cache_key(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        
        return await self.cache_service.get(cache_key)
    
    async def _cache_response(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        response: str,
        provider: BaseLLMProvider
    ):
        """Cache response"""
        if not self.cache_service:
            return
        
        cache_key = self.cache_service.generate_cache_key(
            prompt=prompt,
            model=provider.model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        
        await self.cache_service.set(cache_key, response)
    
    async def _check_rate_limit(self, provider_name: str) -> bool:
        """Check if provider is within rate limit"""
        if not self.rate_limit_manager:
            return True
        
        # Get provider's rate limit (per minute)
        limit = 30  # Default conservative limit
        
        if provider_name == 'groq':
            limit = 30
        elif provider_name == 'gemini':
            limit = 60
        elif provider_name == 'huggingface':
            limit = 30
        
        return await self.rate_limit_manager.check_limit(
            provider_name=provider_name,
            limit=limit,
            window_seconds=60
        )
    
    def _get_provider_order(self, preferred_provider: Optional[str] = None) -> List[BaseLLMProvider]:
        """Get provider order with preferred first"""
        if not preferred_provider:
            return self.providers.copy()
        
        # Move preferred to front
        ordered = []
        for provider in self.providers:
            provider_name = provider.__class__.__name__.replace('Provider', '').lower()
            if provider_name == preferred_provider.lower():
                ordered.insert(0, provider)
            else:
                ordered.append(provider)
        
        return ordered
    
    def _update_provider_stats(self, provider_name: str, success: bool, error: Optional[str] = None):
        """Update provider statistics"""
        if provider_name not in self.stats['provider_usage']:
            self.stats['provider_usage'][provider_name] = {
                'requests': 0,
                'successes': 0,
                'failures': 0
            }
        
        self.stats['provider_usage'][provider_name]['requests'] += 1
        
        if success:
            self.stats['provider_usage'][provider_name]['successes'] += 1
        else:
            self.stats['provider_usage'][provider_name]['failures'] += 1
            
            if error:
                if provider_name not in self.stats['errors']:
                    self.stats['errors'][provider_name] = []
                self.stats['errors'][provider_name].append({
                    'error': error,
                    'timestamp': datetime.utcnow().isoformat()
                })
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = self.stats.copy()
        
        # Add cache statistics
        if self.cache_service:
            stats['cache'] = self.cache_service.get_statistics()
        
        # Add rate limit statistics
        if self.rate_limit_manager:
            stats['rate_limits'] = self.rate_limit_manager.get_statistics()
        
        # Calculate success rates
        for provider_name, usage in stats['provider_usage'].items():
            total = usage['requests']
            if total > 0:
                usage['success_rate'] = round(usage['successes'] / total * 100, 2)
        
        return stats
    
    async def check_providers_availability(self) -> Dict[str, bool]:
        """
        Check availability of all providers.
        
        Returns:
            Dictionary mapping provider names to availability status
        """
        availability = {}
        
        for provider in self.providers:
            provider_name = provider.__class__.__name__.replace('Provider', '').lower()
            try:
                is_available = await provider.check_availability()
                availability[provider_name] = is_available
            except Exception as e:
                logger.error(f"Error checking {provider_name}: {e}")
                availability[provider_name] = False
        
        return availability
    
    async def close(self):
        """Close all connections"""
        if self.rate_limit_manager:
            await self.rate_limit_manager.close()
        
        if self.cache_service:
            await self.cache_service.close()
        
        logger.info("Closed LLM Manager connections")
    
    def __str__(self) -> str:
        provider_names = [p.__class__.__name__.replace('Provider', '') for p in self.providers]
        return f"LLMManager(providers={provider_names}, cache={'On' if self.enable_cache else 'Off'})"


# Convenience function to create LLM manager from environment
def create_llm_manager_from_env() -> LLMManager:
    """
    Create LLM Manager from environment variables.
    
    Returns:
        LLMManager instance with all configured providers
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Create providers
    providers = []
    
    # Try Groq
    groq = create_groq_provider_from_env()
    if groq:
        providers.append(groq)
    
    # Try Gemini
    gemini = create_gemini_provider_from_env()
    if gemini:
        providers.append(gemini)
    
    # Try HuggingFace
    hf = create_huggingface_provider_from_env()
    if hf:
        providers.append(hf)
    
    if not providers:
        logger.error("❌ No LLM providers configured!")
        raise ValueError("No LLM providers configured. Please set API keys in .env")
    
    # Create rate limit manager
    rate_limit_manager = create_rate_limit_manager_from_env()
    
    # Create cache service
    cache_service = create_cache_service_from_env()
    enable_cache = os.getenv("LLM_ENABLE_CACHE", "true").lower() == "true"
    
    # Create manager
    manager = LLMManager(
        providers=providers,
        rate_limit_manager=rate_limit_manager,
        cache_service=cache_service,
        enable_cache=enable_cache,
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "3"))
    )
    
    logger.info(f"✅ LLM Manager created with {len(providers)} providers")
    return manager
