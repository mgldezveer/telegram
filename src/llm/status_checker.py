"""
LLM Provider Status Checker
Проверка доступности и статуса всех провайдеров
"""

import asyncio
import logging
from typing import Dict, List
from datetime import datetime

from .config import get_config
from .providers import (
    GroqProvider,
    GeminiProvider,
    HuggingFaceProvider
)

logger = logging.getLogger(__name__)


class ProviderStatus:
    """Статус провайдера"""
    
    def __init__(
        self,
        name: str,
        enabled: bool,
        available: bool = False,
        response_time: float = 0.0,
        error: str = None
    ):
        self.name = name
        self.enabled = enabled
        self.available = available
        self.response_time = response_time
        self.error = error
        self.checked_at = datetime.now()
    
    def __str__(self) -> str:
        if not self.enabled:
            return f"❌ {self.name}: Disabled"
        
        if self.available:
            return f"✅ {self.name}: Available ({self.response_time:.2f}s)"
        
        error_msg = f" - {self.error}" if self.error else ""
        return f"⚠️ {self.name}: Unavailable{error_msg}"
    
    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'available': self.available,
            'response_time': self.response_time,
            'error': self.error,
            'checked_at': self.checked_at.isoformat()
        }


class StatusChecker:
    """Проверка статуса LLM провайдеров"""
    
    def __init__(self):
        self.config = get_config()
    
    async def check_all_providers(self) -> Dict[str, ProviderStatus]:
        """
        Проверка всех провайдеров.
        
        Returns:
            Словарь {имя_провайдера: ProviderStatus}
        """
        results = {}
        
        # Проверка каждого провайдера
        for provider_name in ['groq', 'gemini', 'huggingface']:
            provider_config = self.config.get_provider_config(provider_name)
            
            if not provider_config or not provider_config.enabled:
                results[provider_name] = ProviderStatus(
                    name=provider_name,
                    enabled=False
                )
                continue
            
            # Проверка доступности
            status = await self._check_provider(provider_name, provider_config)
            results[provider_name] = status
        
        return results
    
    async def _check_provider(self, name: str, config) -> ProviderStatus:
        """
        Проверка одного провайдера.
        
        Args:
            name: Имя провайдера
            config: Конфигурация провайдера
            
        Returns:
            ProviderStatus
        """
        try:
            # Создание провайдера
            provider = self._create_provider(name, config)
            
            if not provider:
                return ProviderStatus(
                    name=name,
                    enabled=True,
                    available=False,
                    error="Failed to create provider"
                )
            
            # Проверка доступности с замером времени
            start_time = datetime.now()
            
            available = await asyncio.wait_for(
                provider.check_availability(),
                timeout=10.0
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return ProviderStatus(
                name=name,
                enabled=True,
                available=available,
                response_time=response_time
            )
            
        except asyncio.TimeoutError:
            return ProviderStatus(
                name=name,
                enabled=True,
                available=False,
                error="Timeout (>10s)"
            )
            
        except Exception as e:
            logger.error(f"Error checking {name}: {e}")
            return ProviderStatus(
                name=name,
                enabled=True,
                available=False,
                error=str(e)
            )
    
    def _create_provider(self, name: str, config):
        """Создание экземпляра провайдера"""
        try:
            if name == 'groq':
                return GroqProvider(
                    api_key=config.api_key,
                    model=config.model
                )
            elif name == 'gemini':
                return GeminiProvider(
                    api_key=config.api_key,
                    model=config.model
                )
            elif name == 'huggingface':
                return HuggingFaceProvider(
                    api_key=config.api_key,
                    model=config.model
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to create {name} provider: {e}")
            return None
    
    async def get_status_report(self) -> str:
        """
        Получение текстового отчета о статусе.
        
        Returns:
            Форматированный отчет
        """
        statuses = await self.check_all_providers()
        
        report = "🔍 LLM Provider Status Report\n"
        report += "=" * 40 + "\n\n"
        
        # Статус каждого провайдера
        for name in ['groq', 'gemini', 'huggingface']:
            status = statuses.get(name)
            if status:
                report += f"{status}\n"
        
        # Итоговая статистика
        enabled_count = sum(1 for s in statuses.values() if s.enabled)
        available_count = sum(1 for s in statuses.values() if s.available)
        
        report += "\n" + "=" * 40 + "\n"
        report += f"Total: {enabled_count} enabled, {available_count} available\n"
        
        # Рекомендации
        if available_count == 0:
            report += "\n⚠️ WARNING: No providers available!\n"
            report += "Check your API keys and network connection.\n"
        elif available_count < enabled_count:
            report += "\n⚠️ Some providers are unavailable.\n"
            report += "System will use fallback providers.\n"
        else:
            report += "\n✅ All enabled providers are available!\n"
        
        return report
    
    def get_available_providers(self, statuses: Dict[str, ProviderStatus]) -> List[str]:
        """
        Получение списка доступных провайдеров.
        
        Args:
            statuses: Словарь статусов
            
        Returns:
            Список имен доступных провайдеров
        """
        return [
            name for name, status in statuses.items()
            if status.enabled and status.available
        ]


# Удобная функция для быстрой проверки
async def check_providers_status() -> Dict[str, ProviderStatus]:
    """
    Быстрая проверка статуса всех провайдеров.
    
    Returns:
        Словарь статусов
    """
    checker = StatusChecker()
    return await checker.check_all_providers()


async def print_status_report():
    """Вывод отчета о статусе в консоль"""
    checker = StatusChecker()
    report = await checker.get_status_report()
    print(report)


# Для запуска из командной строки
if __name__ == "__main__":
    asyncio.run(print_status_report())
