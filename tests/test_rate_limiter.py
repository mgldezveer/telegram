"""
Тесты для Rate Limit Manager
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import time

from src.llm.rate_limit_manager import RateLimitManager, ProviderRateLimiter


@pytest.fixture
def rate_limiter():
    """Фикстура для RateLimitManager (in-memory)"""
    return RateLimitManager(redis_client=None)


@pytest.fixture
def provider_limiter(rate_limiter):
    """Фикстура для ProviderRateLimiter"""
    return ProviderRateLimiter(
        manager=rate_limiter,
        provider="test_provider",
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=1000
    )


class TestRateLimitManager:
    """Тесты для RateLimitManager"""
    
    def test_initialization(self, rate_limiter):
        """Тест инициализации"""
        assert rate_limiter.use_redis is False
        assert isinstance(rate_limiter._memory_store, dict)
        assert isinstance(rate_limiter._locks, dict)
    
    @pytest.mark.asyncio
    async def test_check_limit_initial(self, rate_limiter):
        """Тест проверки лимита при первом запросе"""
        result = await rate_limiter.check_limit(
            provider="test",
            limit_type="minute",
            max_requests=10,
            window_seconds=60
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_record_request(self, rate_limiter):
        """Тест записи запроса"""
        await rate_limiter.record_request(
            provider="test",
            limit_type="minute",
            window_seconds=60
        )
        
        # Проверяем что запрос записан
        remaining = await rate_limiter.get_remaining(
            provider="test",
            limit_type="minute",
            max_requests=10,
            window_seconds=60
        )
        assert remaining == 9
    
    @pytest.mark.asyncio
    async def test_limit_enforcement(self, rate_limiter):
        """Тест применения лимита"""
        max_requests = 5
        
        # Делаем max_requests запросов
        for i in range(max_requests):
            can_proceed = await rate_limiter.check_limit(
                provider="test",
                limit_type="minute",
                max_requests=max_requests,
                window_seconds=60
            )
            assert can_proceed is True
            
            await rate_limiter.record_request(
                provider="test",
                limit_type="minute",
                window_seconds=60
            )
        
        # Следующий запрос должен быть заблокирован
        can_proceed = await rate_limiter.check_limit(
            provider="test",
            limit_type="minute",
            max_requests=max_requests,
            window_seconds=60
        )
        assert can_proceed is False
    
    @pytest.mark.asyncio
    async def test_sliding_window(self, rate_limiter):
        """Тест sliding window algorithm"""
        max_requests = 3
        window_seconds = 2
        
        # Делаем 3 запроса
        for i in range(max_requests):
            await rate_limiter.record_request(
                provider="test",
                limit_type="test",
                window_seconds=window_seconds
            )
        
        # Лимит достигнут
        can_proceed = await rate_limiter.check_limit(
            provider="test",
            limit_type="test",
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        assert can_proceed is False
        
        # Ждем пока окно сдвинется
        await asyncio.sleep(2.1)
        
        # Теперь должно быть доступно
        can_proceed = await rate_limiter.check_limit(
            provider="test",
            limit_type="test",
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        assert can_proceed is True
    
    @pytest.mark.asyncio
    async def test_get_remaining(self, rate_limiter):
        """Тест получения оставшихся запросов"""
        max_requests = 10
        
        # Изначально все доступны
        remaining = await rate_limiter.get_remaining(
            provider="test",
            limit_type="minute",
            max_requests=max_requests,
            window_seconds=60
        )
        assert remaining == max_requests
        
        # Делаем 3 запроса
        for i in range(3):
            await rate_limiter.record_request(
                provider="test",
                limit_type="minute",
                window_seconds=60
            )
        
        # Должно остаться 7
        remaining = await rate_limiter.get_remaining(
            provider="test",
            limit_type="minute",
            max_requests=max_requests,
            window_seconds=60
        )
        assert remaining == 7
    
    @pytest.mark.asyncio
    async def test_reset(self, rate_limiter):
        """Тест сброса лимитов"""
        # Делаем несколько запросов
        for i in range(5):
            await rate_limiter.record_request(
                provider="test",
                limit_type="minute",
                window_seconds=60
            )
        
        # Проверяем что запросы записаны
        remaining = await rate_limiter.get_remaining(
            provider="test",
            limit_type="minute",
            max_requests=10,
            window_seconds=60
        )
        assert remaining == 5
        
        # Сбрасываем
        await rate_limiter.reset("test", "minute")
        
        # Должно быть сброшено
        remaining = await rate_limiter.get_remaining(
            provider="test",
            limit_type="minute",
            max_requests=10,
            window_seconds=60
        )
        assert remaining == 10
    
    @pytest.mark.asyncio
    async def test_reset_all(self, rate_limiter):
        """Тест сброса всех лимитов провайдера"""
        # Делаем запросы для разных типов
        for limit_type in ['minute', 'hour', 'day']:
            await rate_limiter.record_request(
                provider="test",
                limit_type=limit_type,
                window_seconds=60
            )
        
        # Сбрасываем все
        await rate_limiter.reset("test")
        
        # Все должно быть сброшено
        for limit_type in ['minute', 'hour', 'day']:
            remaining = await rate_limiter.get_remaining(
                provider="test",
                limit_type=limit_type,
                max_requests=10,
                window_seconds=60
            )
            assert remaining == 10
    
    @pytest.mark.asyncio
    async def test_get_stats(self, rate_limiter):
        """Тест получения статистики"""
        # Делаем запросы
        await rate_limiter.record_request("test", "minute", 60)
        await rate_limiter.record_request("test", "minute", 60)
        await rate_limiter.record_request("test", "hour", 3600)
        
        stats = await rate_limiter.get_stats("test")
        
        assert stats['minute'] == 2
        assert stats['hour'] == 1
        assert stats['day'] == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter):
        """Тест конкурентных запросов"""
        max_requests = 10
        
        async def make_request():
            can_proceed = await rate_limiter.check_limit(
                provider="test",
                limit_type="minute",
                max_requests=max_requests,
                window_seconds=60
            )
            if can_proceed:
                await rate_limiter.record_request(
                    provider="test",
                    limit_type="minute",
                    window_seconds=60
                )
            return can_proceed
        
        # Делаем 20 конкурентных запросов
        results = await asyncio.gather(*[make_request() for _ in range(20)])
        
        # Только max_requests должны пройти
        assert sum(results) == max_requests
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, rate_limiter):
        """Тест очистки старых данных"""
        # Добавляем данные
        await rate_limiter.record_request("test", "minute", 60)
        
        # Проверяем что данные есть
        assert len(rate_limiter._memory_store) > 0
        
        # Очищаем старые данные (с очень маленьким max_age)
        await asyncio.sleep(0.1)
        await rate_limiter.cleanup_old_data(max_age_seconds=0)
        
        # Данные должны быть удалены
        assert len(rate_limiter._memory_store) == 0


class TestProviderRateLimiter:
    """Тесты для ProviderRateLimiter"""
    
    def test_initialization(self, provider_limiter):
        """Тест инициализации"""
        assert provider_limiter.provider == "test_provider"
        assert provider_limiter.limits['minute'] == (10, 60)
        assert provider_limiter.limits['hour'] == (100, 3600)
        assert provider_limiter.limits['day'] == (1000, 86400)
    
    @pytest.mark.asyncio
    async def test_check_all_limits_pass(self, provider_limiter):
        """Тест проверки всех лимитов (успех)"""
        result = await provider_limiter.check_all_limits()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_all_limits_fail(self, provider_limiter):
        """Тест проверки всех лимитов (провал)"""
        # Исчерпываем минутный лимит
        for i in range(10):
            await provider_limiter.record_request()
        
        result = await provider_limiter.check_all_limits()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_record_request(self, provider_limiter):
        """Тест записи запроса"""
        await provider_limiter.record_request()
        
        remaining = await provider_limiter.get_remaining_all()
        
        assert remaining['minute'] == 9
        assert remaining['hour'] == 99
        assert remaining['day'] == 999
    
    @pytest.mark.asyncio
    async def test_get_remaining_all(self, provider_limiter):
        """Тест получения всех оставшихся запросов"""
        remaining = await provider_limiter.get_remaining_all()
        
        assert remaining['minute'] == 10
        assert remaining['hour'] == 100
        assert remaining['day'] == 1000
    
    @pytest.mark.asyncio
    async def test_reset(self, provider_limiter):
        """Тест сброса лимитов"""
        # Делаем запросы
        for i in range(5):
            await provider_limiter.record_request()
        
        # Сбрасываем
        await provider_limiter.reset()
        
        # Проверяем что сброшено
        remaining = await provider_limiter.get_remaining_all()
        assert remaining['minute'] == 10
        assert remaining['hour'] == 100
        assert remaining['day'] == 1000
    
    @pytest.mark.asyncio
    async def test_multiple_limit_types(self, provider_limiter):
        """Тест работы с несколькими типами лимитов"""
        # Делаем 5 запросов
        for i in range(5):
            await provider_limiter.record_request()
        
        remaining = await provider_limiter.get_remaining_all()
        
        # Все типы лимитов должны уменьшиться
        assert remaining['minute'] == 5
        assert remaining['hour'] == 95
        assert remaining['day'] == 995


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
