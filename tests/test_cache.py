"""
Тесты для Cache Service
"""

import pytest
import asyncio
from datetime import datetime

from src.llm.cache import CacheService, SemanticCache
from src.llm.models import LLMResponse


@pytest.fixture
def cache_service():
    """Фикстура для CacheService (in-memory)"""
    return CacheService(redis_client=None, max_memory_size=10, default_ttl=60)


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
        assert cache_service.max_memory_size == 10
        assert cache_service.default_ttl == 60
        assert cache_service.hits == 0
        assert cache_service.misses == 0
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service, sample_response):
        """Тест сохранения и получения"""
        key = "test_key"
        
        # Сохраняем
        await cache_service.set(key, sample_response)
        
        # Получаем
        result = await cache_service.get(key)
        
        assert result is not None
        assert result.text == sample_response.text
        assert result.provider == sample_response.provider
        assert result.cached is True
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service):
        """Тест промаха кэша"""
        result = await cache_service.get("nonexistent_key")
        
        assert result is None
        assert cache_service.misses == 1
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_service, sample_response):
        """Тест попадания в кэш"""
        key = "test_key"
        
        await cache_service.set(key, sample_response)
        result = await cache_service.get(key)
        
        assert result is not None
        assert cache_service.hits == 1
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_service, sample_response):
        """Тест удаления из кэша"""
        key = "test_key"
        
        await cache_service.set(key, sample_response)
        await cache_service.delete(key)
        
        result = await cache_service.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_clear(self, cache_service, sample_response):
        """Тест очистки кэша"""
        # Добавляем несколько записей
        for i in range(5):
            await cache_service.set(f"key_{i}", sample_response)
        
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
        for i in range(cache_service.max_memory_size):
            await cache_service.set(f"key_{i}", sample_response)
        
        # Добавляем еще один элемент
        await cache_service.set("key_new", sample_response)
        
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
        await cache_service.set(key, sample_response, ttl=1)
        
        # Сразу должно быть доступно
        result = await cache_service.get(key)
        assert result is not None
        
        # Ждем истечения TTL
        await asyncio.sleep(1.1)
        
        # Должно быть удалено
        result = await cache_service.get(key)
        assert result is None
    
    def test_generate_key(self, cache_service):
        """Тест генерации ключа кэша"""
        key1 = cache_service.generate_key(
            provider="groq",
            model="llama-3",
            prompt="Hello world"
        )
        
        key2 = cache_service.generate_key(
            provider="groq",
            model="llama-3",
            prompt="Hello world"
        )
        
        # Одинаковые параметры должны давать одинаковый ключ
        assert key1 == key2
        
        key3 = cache_service.generate_key(
            provider="groq",
            model="llama-3",
            prompt="Different prompt"
        )
        
        # Разные параметры должны давать разные ключи
        assert key1 != key3
    
    def test_generate_key_with_params(self, cache_service):
        """Тест генерации ключа с дополнительными параметрами"""
        key1 = cache_service.generate_key(
            provider="groq",
            model="llama-3",
            prompt="Hello",
            temperature=0.7,
            max_tokens=1000
        )
        
        key2 = cache_service.generate_key(
            provider="groq",
            model="llama-3",
            prompt="Hello",
            temperature=0.8,
            max_tokens=1000
        )
        
        # Разная температура должна давать разные ключи
        assert key1 != key2
    
    def test_get_stats(self, cache_service):
        """Тест получения статистики"""
        stats = cache_service.get_stats()
        
        assert 'total_requests' in stats
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
        assert 'cache_size' in stats
        assert stats['backend'] == 'memory'
    
    @pytest.mark.asyncio
    async def test_stats_calculation(self, cache_service, sample_response):
        """Тест расчета статистики"""
        key = "test_key"
        
        # Сохраняем
        await cache_service.set(key, sample_response)
        
        # 1 hit
        await cache_service.get(key)
        
        # 2 misses
        await cache_service.get("nonexistent_1")
        await cache_service.get("nonexistent_2")
        
        stats = cache_service.get_stats()
        
        assert stats['total_requests'] == 3
        assert stats['hits'] == 1
        assert stats['misses'] == 2
        assert stats['hit_rate'] == 33.33
    
    def test_reset_stats(self, cache_service):
        """Тест сброса статистики"""
        cache_service.hits = 10
        cache_service.misses = 5
        cache_service.total_requests = 15
        
        cache_service.reset_stats()
        
        assert cache_service.hits == 0
        assert cache_service.misses == 0
        assert cache_service.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache_service, sample_response):
        """Тест очистки истекших записей"""
        # Добавляем записи с коротким TTL
        for i in range(3):
            await cache_service.set(f"key_{i}", sample_response, ttl=1)
        
        # Ждем истечения
        await asyncio.sleep(1.1)
        
        # Очищаем
        await cache_service.cleanup_expired()
        
        # Все должно быть удалено
        for i in range(3):
            result = await cache_service.get(f"key_{i}")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache_service, sample_response):
        """Тест конкурентного доступа"""
        async def set_value(key):
            await cache_service.set(key, sample_response)
        
        async def get_value(key):
            return await cache_service.get(key)
        
        # Конкурентная запись
        await asyncio.gather(*[set_value(f"key_{i}") for i in range(10)])
        
        # Конкурентное чтение
        results = await asyncio.gather(*[get_value(f"key_{i}") for i in range(10)])
        
        # Все должно быть записано и прочитано
        assert all(r is not None for r in results)
    
    def test_response_serialization(self, cache_service, sample_response):
        """Тест сериализации/десериализации ответа"""
        # Конвертируем в словарь
        response_dict = cache_service._response_to_dict(sample_response)
        
        assert response_dict['text'] == sample_response.text
        assert response_dict['provider'] == sample_response.provider
        
        # Конвертируем обратно
        restored = cache_service._dict_to_response(response_dict)
        
        assert restored.text == sample_response.text
        assert restored.provider == sample_response.provider
        assert restored.tokens_used == sample_response.tokens_used


class TestSemanticCache:
    """Тесты для SemanticCache"""
    
    @pytest.fixture
    def semantic_cache(self, cache_service):
        """Фикстура для SemanticCache"""
        return SemanticCache(cache_service, similarity_threshold=0.8)
    
    def test_initialization(self, semantic_cache):
        """Тест инициализации"""
        assert semantic_cache.similarity_threshold == 0.8
        assert semantic_cache.cache is not None
    
    def test_calculate_similarity_identical(self, semantic_cache):
        """Тест расчета схожести идентичных текстов"""
        text = "Hello world"
        similarity = semantic_cache.calculate_similarity(text, text)
        
        assert similarity == 1.0
    
    def test_calculate_similarity_different(self, semantic_cache):
        """Тест расчета схожести разных текстов"""
        text1 = "Hello world"
        text2 = "Goodbye universe"
        
        similarity = semantic_cache.calculate_similarity(text1, text2)
        
        assert 0.0 <= similarity < 1.0
    
    def test_calculate_similarity_partial(self, semantic_cache):
        """Тест расчета схожести частично совпадающих текстов"""
        text1 = "Hello world from Python"
        text2 = "Hello world from JavaScript"
        
        similarity = semantic_cache.calculate_similarity(text1, text2)
        
        # Должна быть высокая схожесть (3 из 4 слов совпадают)
        assert similarity > 0.5
    
    @pytest.mark.asyncio
    async def test_find_similar(self, semantic_cache, sample_response):
        """Тест поиска похожего ответа"""
        # Сохраняем ответ
        key = semantic_cache.cache.generate_key(
            provider="test",
            model="test",
            prompt="Hello world"
        )
        await semantic_cache.cache.set(key, sample_response)
        
        # Ищем точное совпадение
        result = await semantic_cache.find_similar(
            prompt="Hello world",
            provider="test",
            model="test"
        )
        
        assert result is not None
        assert result.text == sample_response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
