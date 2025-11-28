"""
LLM Configuration - Centralized configuration management
"""

import logging
import os
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider"""
    name: str
    enabled: bool
    api_key: Optional[str]
    model: str
    priority: int = 0  # Lower number = higher priority
    
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        # HuggingFace doesn't require API key
        if self.name == "huggingface":
            return self.enabled
        return self.enabled and bool(self.api_key)


@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    use_redis: bool = True
    redis_url: str = "redis://localhost:6379/0"
    ttl_seconds: int = 3600
    max_memory_size: int = 1000


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    use_redis: bool = True
    redis_url: str = "redis://localhost:6379/0"


@dataclass
class LLMConfig:
    """
    Complete LLM system configuration.
    
    Loads configuration from environment variables with validation.
    """
    # Providers
    groq: ProviderConfig
    gemini: ProviderConfig
    huggingface: ProviderConfig
    
    # Services
    cache: CacheConfig
    rate_limit: RateLimitConfig
    
    # General settings
    max_retries: int = 3
    default_max_tokens: int = 1000
    default_temperature: float = 0.7
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """
        Load configuration from environment variables.
        
        Returns:
            LLMConfig instance
        """
        load_dotenv()
        
        # Groq configuration
        groq = ProviderConfig(
            name="groq",
            enabled=os.getenv("LLM_GROQ_ENABLED", "true").lower() == "true",
            api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            priority=int(os.getenv("LLM_GROQ_PRIORITY", "1"))
        )
        
        # Gemini configuration
        gemini = ProviderConfig(
            name="gemini",
            enabled=os.getenv("LLM_GEMINI_ENABLED", "true").lower() == "true",
            api_key=os.getenv("GEMINI_API_KEY"),
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            priority=int(os.getenv("LLM_GEMINI_PRIORITY", "2"))
        )
        
        # HuggingFace configuration
        huggingface = ProviderConfig(
            name="huggingface",
            enabled=os.getenv("LLM_HUGGINGFACE_ENABLED", "true").lower() == "true",
            api_key=os.getenv("HUGGINGFACE_API_KEY"),  # Optional
            model=os.getenv("HUGGINGFACE_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
            priority=int(os.getenv("LLM_HUGGINGFACE_PRIORITY", "3"))
        )
        
        # Cache configuration
        cache = CacheConfig(
            enabled=os.getenv("LLM_ENABLE_CACHE", "true").lower() == "true",
            use_redis=os.getenv("LLM_USE_REDIS", "true").lower() == "true",
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            ttl_seconds=int(os.getenv("LLM_CACHE_TTL", "3600")),
            max_memory_size=int(os.getenv("LLM_CACHE_MAX_SIZE", "1000"))
        )
        
        # Rate limit configuration
        rate_limit = RateLimitConfig(
            enabled=os.getenv("LLM_RATE_LIMIT_ENABLED", "true").lower() == "true",
            use_redis=os.getenv("LLM_USE_REDIS", "true").lower() == "true",
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )
        
        # General settings
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        default_max_tokens = int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "1000"))
        default_temperature = float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7"))
        
        return cls(
            groq=groq,
            gemini=gemini,
            huggingface=huggingface,
            cache=cache,
            rate_limit=rate_limit,
            max_retries=max_retries,
            default_max_tokens=default_max_tokens,
            default_temperature=default_temperature
        )
    
    def get_enabled_providers(self) -> List[ProviderConfig]:
        """
        Get list of enabled and configured providers in priority order.
        
        Returns:
            List of ProviderConfig sorted by priority
        """
        providers = [self.groq, self.gemini, self.huggingface]
        enabled = [p for p in providers if p.is_configured()]
        return sorted(enabled, key=lambda p: p.priority)
    
    def validate(self) -> Dict[str, List[str]]:
        """
        Validate configuration and return any issues.
        
        Returns:
            Dictionary mapping provider names to list of issues
        """
        issues = {}
        
        # Check if at least one provider is configured
        enabled_providers = self.get_enabled_providers()
        if not enabled_providers:
            issues['general'] = ["No LLM providers are configured. Please set at least one API key."]
        
        # Validate individual providers
        for provider in [self.groq, self.gemini, self.huggingface]:
            provider_issues = []
            
            if provider.enabled and not provider.is_configured():
                if provider.name != "huggingface":
                    provider_issues.append(f"Provider enabled but API key not set")
            
            if provider.priority < 0:
                provider_issues.append(f"Invalid priority: {provider.priority}")
            
            if provider_issues:
                issues[provider.name] = provider_issues
        
        # Validate cache settings
        if self.cache.enabled and self.cache.use_redis:
            if not self.cache.redis_url:
                issues['cache'] = ["Redis enabled but URL not set"]
        
        # Validate rate limit settings
        if self.rate_limit.enabled and self.rate_limit.use_redis:
            if not self.rate_limit.redis_url:
                issues['rate_limit'] = ["Redis enabled but URL not set"]
        
        return issues
    
    def get_status_summary(self) -> str:
        """
        Get human-readable status summary.
        
        Returns:
            Formatted status string
        """
        lines = ["LLM Configuration Status:"]
        lines.append("")
        
        # Providers
        lines.append("Providers:")
        for provider in [self.groq, self.gemini, self.huggingface]:
            status = "✅ Configured" if provider.is_configured() else "❌ Not configured"
            priority = f"(Priority: {provider.priority})" if provider.is_configured() else ""
            lines.append(f"  {provider.name.capitalize()}: {status} {priority}")
        
        lines.append("")
        
        # Services
        lines.append("Services:")
        cache_status = "✅ Enabled" if self.cache.enabled else "❌ Disabled"
        cache_backend = f"(Redis)" if self.cache.use_redis else "(Memory)"
        lines.append(f"  Cache: {cache_status} {cache_backend}")
        
        rate_limit_status = "✅ Enabled" if self.rate_limit.enabled else "❌ Disabled"
        rate_limit_backend = f"(Redis)" if self.rate_limit.use_redis else "(Memory)"
        lines.append(f"  Rate Limiting: {rate_limit_status} {rate_limit_backend}")
        
        lines.append("")
        
        # Settings
        lines.append("Settings:")
        lines.append(f"  Max Retries: {self.max_retries}")
        lines.append(f"  Default Max Tokens: {self.default_max_tokens}")
        lines.append(f"  Default Temperature: {self.default_temperature}")
        
        # Validation
        issues = self.validate()
        if issues:
            lines.append("")
            lines.append("⚠️ Configuration Issues:")
            for component, component_issues in issues.items():
                for issue in component_issues:
                    lines.append(f"  - {component}: {issue}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        enabled_count = len(self.get_enabled_providers())
        return f"LLMConfig(providers={enabled_count}, cache={'On' if self.cache.enabled else 'Off'}, rate_limit={'On' if self.rate_limit.enabled else 'Off'})"


# Global configuration instance
_config: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """
    Get global LLM configuration instance.
    
    Returns:
        LLMConfig instance
    """
    global _config
    if _config is None:
        _config = LLMConfig.from_env()
        logger.info("✅ LLM configuration loaded")
        
        # Log validation issues
        issues = _config.validate()
        if issues:
            logger.warning("⚠️ Configuration validation issues found:")
            for component, component_issues in issues.items():
                for issue in component_issues:
                    logger.warning(f"  - {component}: {issue}")
    
    return _config


def reload_config():
    """Reload configuration from environment"""
    global _config
    _config = None
    return get_config()
