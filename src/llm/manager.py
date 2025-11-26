"""
LLM Manager - Orchestrates multiple LLM providers
"""

import logging
from typing import List, Optional, Dict
import time
import asyncio

from .base_provider import BaseLLMProvider, RateLimitError, APIError
from .models import LLMResponse, ProviderStatus
from .cache import CacheService
from .rate_limiter import RateLimitManager
from .metrics import get_metrics

logger = logging.getLogger(__name__)


class LLMManager:
    """
    Manages multiple LLM providers with automatic fallback,
    rate limiting, and caching.
    
    Features:
    - Automatic provider fallback on errors
    - Rate limiting per provider
    - Response caching
    - Retry with exponential backoff
    - Provider health monitoring
    """
    
    def __init__(
        self,
        providers: List[BaseLLMProvider],
        cache_service: Optional[CacheService] = None,
        rate_limiter: Optional[RateLimitManager] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize LLM Manager with list of providers.
        
        Args:
            providers: List of LLM provider instances
            cache_service: Optional cache service
            rate_limiter: Optional rate limiter
            max_retries: Maximum retry attempts per provider
            retry_delay: Initial retry delay in seconds
        """
        self.providers = providers
        self.current_provider_index = 0
        self.provider_stats: Dict[str, dict] = {}
        
        # Optional services
        self.cache = cache_service
        self.rate_limiter = rate_limiter
        
        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize stats for each provider
        for provider in providers:
            provider_name = provider.get_provider_name()
            self.provider_stats[provider_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'cache_hits': 0,
                'total_tokens': 0,
                'total_time': 0.0
            }
        
        logger.info(f"LLM Manager initialized with {len(providers)} providers")
        logger.info(f"  Cache: {'enabled' if cache_service else 'disabled'}")
        logger.info(f"  Rate Limiter: {'enabled' if rate_limiter else 'disabled'}")
        for provider in providers:
            logger.info(f"  - {provider.get_provider_name()}: {provider.get_model_name()}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        use_cache: bool = True
    ) -> LLMResponse:
        """
        Generate text using available providers with automatic fallback.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt
            use_cache: Whether to use cache
            
        Returns:
            LLMResponse with generated text
            
        Raises:
            Exception: If all providers fail
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache and self.cache:
            provider = self.providers[self.current_provider_index]
            cache_key = self.cache.generate_key(
                provider=provider.get_provider_name(),
                model=provider.get_model_name(),
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                provider_name = provider.get_provider_name()
                self.provider_stats[provider_name]['cache_hits'] += 1
                
                # Record cache hit
                metrics = get_metrics()
                metrics.record_cache_hit()
                
                logger.info(f"💾 Cache HIT for {provider_name}")
                return cached_response
            else:
                # Record cache miss
                metrics = get_metrics()
                metrics.record_cache_miss()
        
        # Try each provider with retries
        last_error = None
        
        for provider_attempt in range(len(self.providers)):
            provider = self.providers[self.current_provider_index]
            provider_name = provider.get_provider_name()
            
            # Update stats
            self.provider_stats[provider_name]['total_requests'] += 1
            
            # Try with retries
            for retry in range(self.max_retries):
                try:
                    logger.info(f"Attempting generation with {provider_name} (attempt {retry + 1}/{self.max_retries})")
                    
                    # Generate text
                    text = await provider.generate(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system_prompt=system_prompt
                    )
                    
                    generation_time = time.time() - start_time
                    
                    # Create response
                    response = LLMResponse(
                        text=text,
                        provider=provider_name,
                        model=provider.get_model_name(),
                        tokens_used=len(text.split()),  # Approximate
                        generation_time=generation_time,
                        cached=False
                    )
                    
                    # Update stats
                    self.provider_stats[provider_name]['successful_requests'] += 1
                    self.provider_stats[provider_name]['total_tokens'] += response.tokens_used
                    self.provider_stats[provider_name]['total_time'] += generation_time
                    
                    # Record metrics
                    metrics = get_metrics()
                    metrics.record_request(
                        provider=provider_name,
                        success=True,
                        duration=generation_time,
                        tokens=response.tokens_used
                    )
                    
                    # Cache the response
                    if use_cache and self.cache:
                        await self.cache.set(cache_key, response)
                    
                    logger.info(f"✅ Generation successful with {provider_name} in {generation_time:.2f}s")
                    return response
                    
                except RateLimitError as e:
                    logger.warning(f"⚠️ Rate limit reached for {provider_name}")
                    last_error = e
                    self.provider_stats[provider_name]['failed_requests'] += 1
                    
                    # Record metrics
                    metrics = get_metrics()
                    metrics.record_rate_limit_hit(provider_name)
                    metrics.record_request(
                        provider=provider_name,
                        success=False,
                        duration=time.time() - start_time,
                        error="Rate limit exceeded"
                    )
                    
                    break  # Switch to next provider immediately
                    
                except APIError as e:
                    logger.error(f"❌ API error with {provider_name}: {e}")
                    last_error = e
                    self.provider_stats[provider_name]['failed_requests'] += 1
                    
                    # Record metrics
                    metrics = get_metrics()
                    metrics.record_request(
                        provider=provider_name,
                        success=False,
                        duration=time.time() - start_time,
                        error=str(e)
                    )
                    
                    # Retry with exponential backoff
                    if retry < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** retry)
                        logger.info(f"Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        break  # Max retries reached, switch provider
                    
                except Exception as e:
                    logger.error(f"❌ Unexpected error with {provider_name}: {e}")
                    last_error = e
                    self.provider_stats[provider_name]['failed_requests'] += 1
                    
                    # Record metrics
                    metrics = get_metrics()
                    metrics.record_request(
                        provider=provider_name,
                        success=False,
                        duration=time.time() - start_time,
                        error=str(e)
                    )
                    
                    # Retry with exponential backoff
                    if retry < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** retry)
                        logger.info(f"Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        break
            
            # Switch to next provider
            self._switch_to_next_provider()
        
        # All providers failed
        error_msg = f"All providers failed after {len(self.providers)} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def get_available_providers(self) -> List[str]:
        """
        Get list of available provider names.
        
        Returns:
            List of provider names
        """
        available = []
        for provider in self.providers:
            if await provider.check_availability():
                available.append(provider.get_provider_name())
        return available
    
    async def get_provider_status(self, provider_name: str) -> Optional[ProviderStatus]:
        """
        Get status of a specific provider.
        
        Args:
            provider_name: Name of provider
            
        Returns:
            ProviderStatus or None if not found
        """
        for provider in self.providers:
            if provider.get_provider_name() == provider_name:
                return await provider.get_status()
        return None
    
    async def get_all_provider_statuses(self) -> List[ProviderStatus]:
        """
        Get status of all providers.
        
        Returns:
            List of ProviderStatus objects
        """
        statuses = []
        for provider in self.providers:
            status = await provider.get_status()
            statuses.append(status)
        return statuses
    
    def switch_provider(self, provider_name: str) -> bool:
        """
        Manually switch to a specific provider.
        
        Args:
            provider_name: Name of provider to switch to
            
        Returns:
            True if switched successfully, False otherwise
        """
        for i, provider in enumerate(self.providers):
            if provider.get_provider_name() == provider_name:
                self.current_provider_index = i
                logger.info(f"Switched to provider: {provider_name}")
                return True
        
        logger.warning(f"Provider not found: {provider_name}")
        return False
    
    def _switch_to_next_provider(self):
        """Switch to the next provider in the list"""
        self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
        next_provider = self.providers[self.current_provider_index]
        logger.info(f"Switched to next provider: {next_provider.get_provider_name()}")
    
    def get_current_provider(self) -> BaseLLMProvider:
        """Get the currently active provider"""
        return self.providers[self.current_provider_index]
    
    def get_current_provider_name(self) -> str:
        """Get the name of currently active provider"""
        return self.get_current_provider().get_provider_name()
    
    def get_stats(self) -> Dict[str, dict]:
        """
        Get statistics for all providers.
        
        Returns:
            Dictionary with stats for each provider
        """
        stats = {}
        
        for provider_name, provider_stats in self.provider_stats.items():
            total = provider_stats['total_requests']
            success_rate = (provider_stats['successful_requests'] / total * 100) if total > 0 else 0
            avg_time = (provider_stats['total_time'] / provider_stats['successful_requests']) if provider_stats['successful_requests'] > 0 else 0
            
            stats[provider_name] = {
                **provider_stats,
                'success_rate': round(success_rate, 2),
                'avg_response_time': round(avg_time, 2)
            }
        
        # Add cache stats if available
        if self.cache:
            stats['cache'] = self.cache.get_stats()
        
        return stats
    
    def reset_stats(self):
        """Reset all statistics."""
        for provider_name in self.provider_stats:
            self.provider_stats[provider_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'cache_hits': 0,
                'total_tokens': 0,
                'total_time': 0.0
            }
        
        if self.cache:
            self.cache.reset_stats()
        
        logger.info("Statistics reset")
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all providers.
        
        Returns:
            Dictionary with health status for each provider
        """
        health = {}
        
        for provider in self.providers:
            provider_name = provider.get_provider_name()
            try:
                is_available = await provider.check_availability()
                health[provider_name] = is_available
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
                health[provider_name] = False
        
        return health
    
    def __str__(self) -> str:
        provider_names = [p.get_provider_name() for p in self.providers]
        current = self.get_current_provider_name()
        return f"LLMManager(providers={provider_names}, current={current})"
