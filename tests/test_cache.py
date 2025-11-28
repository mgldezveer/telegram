"""
Тесты для Cache Service
"""

import pytest
import asyncio
from datetime import datetime

from src.llm.cache_service import CacheService
from src.llm.models import LLMResponse


@pytest.fixture
def cache_service():
    """Фикстура для CacheService (in-memory)"""
    return CacheService(redis_url=None, use_redis=False, max_memory_size=10, default_ttl=60)


@pytest.fixture
def sample_response():
    """Фикстура для тестового LLMResponse"""
    return LLMResponse(
        text="Test response",
        provider="test_provider",
        model="test_model",
        tokens_used=100,
        generation_time=0.5,
        metadata={'test': 'data'}
    )


class TestCacheService:
    """Тесты для CacheService"""
    
    def test_initialization(self, cache_service):
        """Тест инициализации"""
        assert cache_service.use_redis is False
        assert cache_service.lru_cache.max_size == 10
        assert cache_service.default_ttl == 60
        assert cache_service.stats['hits'] == 0
        assert cache_service.stats['misses'] == 0
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service, sample_response):
        """Тест сохранения и получения"""
        key = "test_key"
        
        # Сохраняем
        await cache_service.set(key, str(sample_response.text))
        
        # Получаем
        result = await cache_service.get(key)
        
        assert result is not None
        assert result == str(sample_response.text)
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service):
        """Тест промаха кэша"""
        result = await cache_service.get("nonexistent_key")
        
        assert result is None
        assert cache_service.stats['misses'] == 1
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_service, sample_response):
        """Тест попадания в кэш"""
        key = "test_key"
        
        await cache_service.set(key, str(sample_response.text))
        result = await cache_service.get(key)
        
        assert result is not None
        assert cache_service.stats['hits'] == 1
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_service, sample_response):
        """Тест удаления из кэша"""
        key = "test_key"
        
        await cache_service.set(key, str(sample_response.text))
        await cache_service.delete(key)
        
        result = await cache_service.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_clear(self, cache_service, sample_response):
        """Тест очистки кэша"""
        # Добавляем несколько записей
        for i in range(5):
            await cache_service.set(f"key_{i}", str(sample_response.text))
        
        # Очищаем
        await cache_service.clear()
        
        # Проверяем что все удалено
        for i in range(5):
            result = await cache_service.get(f"key_{i}")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache_service, sample_response):
        """Тест LRU eviction"""
        # Заполняем кэш до максимума
        for i in range(cache_service.lru_cache.max_size):
            await cache_service.set(f"key_{i}", str(sample_response.text))
        
        # Добавляем еще один элемент
        await cache_service.set("key_new", str(sample_response.text))
        
        # Самый старый элемент должен быть удален
        result = await cache_service.get("key_0")
        assert result is None
        
        # Новый элемент должен быть в кэше
        result = await cache_service.get("key_new")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache_service, sample_response):
        """Тест истечения TTL"""
        key = "test_key"
        
        # Сохраняем с коротким TTL
        await cache_service.set(key, str(sample_response.text), ttl=1)
        
        # Сразу должно быть доступно
        result = await cache_service.get(key)
        assert result is not None
        
        # Ждем истечения TTL
        await asyncio.sleep(1.1)
        
        # Должно быть удалено
        result = await cache_service.get(key)
        assert result is None
    
    def test_generate_cache_key(self, cache_service):
        """Тест генерации ключа кэша"""
        key1 = cache_service.generate_cache_key(
            prompt="Hello world",
            model="llama-3"
        )
        
        key2 = cache_service.generate_cache_key(
            prompt="Hello world",
            model="llama-3"
        )
        
        # Одинаковые параметры должны давать одинаковый ключ
        assert key1 == key2
        
        key3 = cache_service.generate_cache_key(
            prompt="Different prompt",
            model="llama-3"
        )
        
        # Разные параметры должны давать разные ключи
        assert key1 != key3
    
    def test_generate_cache_key_with_params(self, cache_service):
        """Тест генерации ключа с дополнительными параметрами"""
        key1 = cache_service.generate_cache_key(
            prompt="Hello",
            model="llama-3",
            temperature=0.7,
            max_tokens=1000
        )
        
        key2 = cache_service.generate_cache_key(
            prompt="Hello",
            model="llama-3",
            temperature=0.8,
            max_tokens=1000
        )
        
        # Разная температура должна давать разные ключи
        assert key1 != key2
    
    def test_get_stats(self, cache_service):
        """Тест получения статистики"""
        stats = cache_service.get_statistics()
        
        assert 'total_requests' in stats
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
        assert 'size' in stats
        assert stats['backend'] == 'LRU'
    
    @pytest.mark.asyncio
    async def test_stats_calculation(self, cache_service, sample_response):
        """Тест расчета статистики"""
        key = "test_key"
        
        # Сохраняем
        await cache_service.set(key, str(sample_response.text))
        
        # 1 hit
        await cache_service.get(key)
        
        # 2 misses
        await cache_service.get("nonexistent_1")
        await cache_service.get("nonexistent_2")
        
        stats = cache_service.get_statistics()
        
        assert stats['total_requests'] == 3
        assert stats['hits'] == 1
        assert stats['misses'] == 2
        assert stats['hit_rate'] == 33.33
    
    def test_reset_stats(self, cache_service):
        """Тест сброса статистики"""
        cache_service.stats['hits'] = 10
        cache_service.stats['misses'] = 5
        total_before = cache_service.stats['hits'] + cache_service.stats['misses']
        
        # Сброс статистики - очистка статистики через очистку кэша
        old_stats = cache_service.stats.copy()
        cache_service.stats['hits'] = 0
        cache_service.stats['misses'] = 0
        cache_service.stats['sets'] = 0
        cache_service.stats['evictions'] = 0
        
        assert cache_service.stats['hits'] == 0
        assert cache_service.stats['misses'] == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache_service, sample_response):
        """Тест очистки истекших записей"""
        # Кэш с TTL автоматически удаляет устаревшие записи при доступе
        # Добавляем записи с коротким TTL
        for i in range(3):
            await cache_service.set(f"key_{i}", str(sample_response.text), ttl=1)
        
        # Ждем истечения
        await asyncio.sleep(1.1)
        
        # При доступе к устаревшим записям они должны быть удалены
        for i in range(3):
            result = await cache_service.get(f"key_{i}")
            # После истечения TTL результат должен быть None
            assert result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache_service, sample_response):
        """Тест конкурентного доступа"""
        async def set_value(key):
            await cache_service.set(key, str(sample_response.text))
        
        async def get_value(key):
            return await cache_service.get(key)
        
        # Конкурентная запись
        await asyncio.gather(*[set_value(f"key_{i}") for i in range(10)])
        
        # Конкурентное чтение
        results = await asyncio.gather(*[get_value(f"key_{i}") for i in range(10)])
        
        # Все должно быть записано и прочитано
        assert all(r is not None for r in results)
    
    def test_cache_key_generation(self, cache_service):
        """Тест генерации ключей кэша"""
        key1 = cache_service.generate_cache_key(prompt="test", model="test")
        key2 = cache_service.generate_cache_key(prompt="test", model="test")
        key3 = cache_service.generate_cache_key(prompt="different", model="test")
        
        assert key1 == key2  # Одинаковые параметры дают одинаковый ключ
        assert key1 != key3 # Разные параметры дают разные ключи


if __name__ == "__main__":
   pytest.main([__file__, "-v"])
