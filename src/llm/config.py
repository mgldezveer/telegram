"""
LLM Configuration Management
Загрузка и валидация настроек для LLM провайдеров
"""

import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Конфигурация для одного провайдера"""
    name: str
    enabled: bool
    api_key: Optional[str]
    model: Optional[str]
    priority: int = 0
    
    def is_valid(self) -> bool:
        """Проверка валидности конфигурации"""
        if not self.enabled:
            return True  # Отключенный провайдер валиден
        
        if not self.api_key:
            logger.warning(f"⚠️ Provider {self.name}: API key not configured")
            return False
        
        return True


@dataclass
class LLMConfig:
    """
    Конфигурация LLM системы
    
    Загружает настройки из переменных окружения и валидирует их.
    """
    
    # Провайдеры
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    
    # Общие настройки
    default_provider: Optional[str] = None
    fallback_enabled: bool = True
    cache_enabled: bool = True
    rate_limit_enabled: bool = True
    
    # Настройки кэша
    cache_ttl: int = 3600  # 1 час
    cache_max_size: int = 1000
    
    # Настройки retry
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Таймауты
    request_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """
        Загрузка конфигурации из переменных окружения.
        
        Returns:
            LLMConfig с загруженными настройками
        """
        load_dotenv()
        
        config = cls()
        
        # Загрузка провайдеров
        config._load_providers()
        
        # Загрузка общих настроек
        config.default_provider = os.getenv('LLM_DEFAULT_PROVIDER', 'groq')
        config.fallback_enabled = os.getenv('LLM_FALLBACK_ENABLED', 'true').lower() == 'true'
        config.cache_enabled = os.getenv('LLM_CACHE_ENABLED', 'true').lower() == 'true'
        config.rate_limit_enabled = os.getenv('LLM_RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        
        # Настройки кэша
        config.cache_ttl = int(os.getenv('LLM_CACHE_TTL', '3600'))
        config.cache_max_size = int(os.getenv('LLM_CACHE_MAX_SIZE', '1000'))
        
        # Настройки retry
        config.max_retries = int(os.getenv('LLM_MAX_RETRIES', '3'))
        config.retry_delay = float(os.getenv('LLM_RETRY_DELAY', '1.0'))
        
        # Таймауты
        config.request_timeout = int(os.getenv('LLM_REQUEST_TIMEOUT', '30'))
        
        logger.info("✅ LLM configuration loaded from environment")
        return config
    
    def _load_providers(self):
        """Загрузка конфигурации провайдеров"""
        
        # Groq
        self.providers['groq'] = ProviderConfig(
            name='groq',
            enabled=os.getenv('LLM_GROQ_ENABLED', 'true').lower() == 'true',
            api_key=os.getenv('GROQ_API_KEY'),
            model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            priority=int(os.getenv('LLM_GROQ_PRIORITY', '1'))
        )
        
        # Gemini
        self.providers['gemini'] = ProviderConfig(
            name='gemini',
            enabled=os.getenv('LLM_GEMINI_ENABLED', 'false').lower() == 'true',
            api_key=os.getenv('GEMINI_API_KEY'),
            model=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
            priority=int(os.getenv('LLM_GEMINI_PRIORITY', '2'))
        )
        
        # Hugging Face
        self.providers['huggingface'] = ProviderConfig(
            name='huggingface',
            enabled=os.getenv('LLM_HF_ENABLED', 'false').lower() == 'true',
            api_key=os.getenv('HF_API_KEY'),
            model=os.getenv('HF_MODEL'),  # None = использовать список по умолчанию
            priority=int(os.getenv('LLM_HF_PRIORITY', '3'))
        )
    
    def validate(self) -> bool:
        """
        Валидация конфигурации.
        
        Returns:
            True если конфигурация валидна
        """
        # Проверка наличия хотя бы одного включенного провайдера
        enabled_providers = [p for p in self.providers.values() if p.enabled]
        
        if not enabled_providers:
            logger.error("❌ No LLM providers enabled!")
            return False
        
        # Валидация каждого провайдера
        valid_providers = []
        for provider in enabled_providers:
            if provider.is_valid():
                valid_providers.append(provider.name)
            else:
                logger.warning(f"⚠️ Provider {provider.name} is enabled but not valid")
        
        if not valid_providers:
            logger.error("❌ No valid LLM providers configured!")
            return False
        
        logger.info(f"✅ Valid providers: {', '.join(valid_providers)}")
        
        # Проверка default provider
        if self.default_provider and self.default_provider not in valid_providers:
            logger.warning(
                f"⚠️ Default provider '{self.default_provider}' is not valid, "
                f"using first available: {valid_providers[0]}"
            )
            self.default_provider = valid_providers[0]
        
        return True
    
    def get_enabled_providers(self) -> List[str]:
        """
        Получение списка включенных и валидных провайдеров.
        
        Returns:
            Список имен провайдеров
        """
        return [
            name for name, config in self.providers.items()
            if config.enabled and config.is_valid()
        ]
    
    def get_provider_priority_order(self) -> List[str]:
        """
        Получение провайдеров в порядке приоритета.
        
        Returns:
            Список имен провайдеров, отсортированных по приоритету
        """
        enabled = [
            (name, config) for name, config in self.providers.items()
            if config.enabled and config.is_valid()
        ]
        
        # Сортировка по приоритету (меньше = выше приоритет)
        sorted_providers = sorted(enabled, key=lambda x: x[1].priority)
        
        return [name for name, _ in sorted_providers]
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """
        Получение конфигурации провайдера.
        
        Args:
            provider_name: Имя провайдера
            
        Returns:
            ProviderConfig или None
        """
        return self.providers.get(provider_name)
    
    def __str__(self) -> str:
        enabled = self.get_enabled_providers()
        return (
            f"LLMConfig(providers={len(enabled)}, "
            f"default={self.default_provider}, "
            f"cache={self.cache_enabled}, "
            f"fallback={self.fallback_enabled})"
        )


# Глобальный экземпляр конфигурации
_config: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """
    Получение глобального экземпляра конфигурации.
    
    Returns:
        LLMConfig
    """
    global _config
    
    if _config is None:
        _config = LLMConfig.from_env()
        
        if not _config.validate():
            raise ValueError("Invalid LLM configuration")
    
    return _config


def reload_config() -> LLMConfig:
    """
    Перезагрузка конфигурации из окружения.
    
    Returns:
        Новый LLMConfig
    """
    global _config
    _config = None
    return get_config()
