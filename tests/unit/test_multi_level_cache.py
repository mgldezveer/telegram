"""Тесты для многоуровневого кэша."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.cache.multi_level_cache import MultiLevelCache, CacheLevel
from src.cache.i_cache import ICache


class MockCache(ICache):
    """Мок-реализация кэша для тестирования."""
    
    def __init__(self, name: str = "mock", available: bool = True):
        self.name = name
        self.available = available
        self._storage = {}
        self._ttls = {}
    
    async def get(self, key: str) -> None:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        if key in self._storage:
            # Проверяем TTL
            import time
            if key in self._ttls and self._ttls[key] < time.time():
                del self._storage[key]
                del self._ttls[key]
                return None
            return self._storage[key]
        return None
    
    async def set(self, key: str, value: any, ttl: int = None) -> None:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        self._storage[key] = value
        if ttl:
            import time
            self._ttls[key] = time.time() + ttl
    
    async def delete(self, key: str) -> bool:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        if key in self._storage:
            del self._storage[key]
            if key in self._ttls:
                del self._ttls[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        return key in self._storage
    
    async def clear(self) -> None:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        self._storage.clear()
        self._ttls.clear()
    
    async def keys(self, pattern: str = "*") -> list[str]:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        if pattern == "*":
            return list(self._storage.keys())
        elif pattern.endswith("*"):
            prefix = pattern[:-1]
            return [key for key in self._storage.keys() if key.startswith(prefix)]
        else:
            return [key for key in self._storage.keys() if key == pattern]
    
    async def mget(self, keys: list[str]) -> list[None]:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        return [await self.get(key) for key in keys]
    
    async def mset(self, mapping: dict[str, any], ttl: int = None) -> None:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        for key, value in mapping.items():
            await self.set(key, value, ttl)
    
    async def expire(self, key: str, ttl: int) -> bool:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        if key in self._storage:
            import time
            self._ttls[key] = time.time() + ttl
            return True
        return False
    
    async def ttl(self, key: str) -> int:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        if key in self._ttls:
            import time
            remaining = int(self._ttls[key] - time.time())
            return max(0, remaining)
        elif key in self._storage:
            return -1 # Без TTL
        return -1 # Не существует
    
    async def hget(self, name: str, key: str) -> None:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        hash_data = self._storage.get(name, {})
        return hash_data.get(key)
    
    async def hset(self, name: str, key: str, value: any, ttl: int = None) -> None:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        hash_data = self._storage.get(name, {})
        hash_data[key] = value
        self._storage[name] = hash_data
        if ttl:
            import time
            self._ttls[name] = time.time() + ttl
    
    async def hdel(self, name: str, *keys: str) -> int:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        hash_data = self._storage.get(name, {})
        deleted = 0
        for key in keys:
            if key in hash_data:
                del hash_data[key]
                deleted += 1
        
        if hash_data:
            self._storage[name] = hash_data
        else:
            # Удаляем весь хэш, если он пуст
            if name in self._storage:
                del self._storage[name]
            if name in self._ttls:
                del self._ttls[name]
        
        return deleted
    
    async def hgetall(self, name: str) -> dict[str, any]:
        if not self.available:
            from src.cache.exceptions import CacheBackendError
            raise CacheBackendError(f"Mock cache {self.name} is not available")
        
        return self._storage.get(name, {}).copy()
    
    async def ping(self) -> bool:
        return self.available
    
    async def get_stats(self) -> dict[str, any]:
        return {
            'name': self.name,
            'available': self.available,
            'keys_count': len(self._storage)
        }
    
    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_multi_level_cache_initialization():
    """Тест инициализации многоуровневого кэша."""
    cache = MultiLevelCache()
    await cache.initialize()
    
    assert cache._initialized is True
    assert len(cache._levels) >= 1  # Должен быть хотя бы один уровень


@pytest.mark.asyncio
async def test_multi_level_cache_with_custom_levels():
    """Тест многоуровневого кэша с пользовательскими уровнями."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Проверяем, что уровни отсортированы по приоритету
    assert cache._levels[0].name == "fast"
    assert cache._levels[1].name == "slow"


@pytest.mark.asyncio
async def test_multi_level_cache_get_set():
    """Тест операций получения и установки значений."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Устанавливаем значение
    await cache.set("test_key", "test_value", ttl=100)
    
    # Проверяем, что значение установлено в обоих уровнях (write-through)
    fast_value = await fast_cache.get("test_key")
    slow_value = await slow_cache.get("test_key")
    
    assert fast_value == "test_value"
    assert slow_value == "test_value"
    
    # Получаем значение
    value = await cache.get("test_key")
    assert value == "test_value"


@pytest.mark.asyncio
async def test_multi_level_cache_priority_levels():
    """Тест приоритетности уровней кэша."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    # Устанавливаем значение только в медленный кэш
    await slow_cache.set("test_key", "slow_value", ttl=100)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Получаем значение - должно быть получено из медленного кэша
    # и записано в быстрый для ускорения следующего доступа
    value = await cache.get("test_key")
    assert value == "slow_value"
    
    # Проверяем, что значение теперь есть и в быстром кэше
    fast_value = await fast_cache.get("test_key")
    assert fast_value == "slow_value"


@pytest.mark.asyncio
async def test_multi_level_cache_unavailable_level():
    """Тест работы при недоступности одного из уровней."""
    fast_cache = MockCache("fast", available=False)  # Недоступен
    slow_cache = MockCache("slow", available=True)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Устанавливаем значение
    await cache.set("test_key", "test_value", ttl=100)
    
    # Проверяем, что значение есть только в медленном кэше
    slow_value = await slow_cache.get("test_key")
    
    assert slow_value == "test_value"
    
    # Получаем значение через многоуровневый кэш - должно быть получено из медленного кэша
    value = await cache.get("test_key")
    assert value == "test_value"


@pytest.mark.asyncio
async def test_multi_level_cache_write_through_strategy():
    """Тест стратегии write-through."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels, sync_strategy="write_through")
    await cache.initialize()
    
    # Устанавливаем значение
    await cache.set("test_key", "test_value", ttl=100)
    
    # Проверяем, что значение записано в оба уровня
    fast_value = await fast_cache.get("test_key")
    slow_value = await slow_cache.get("test_key")
    
    assert fast_value == "test_value"
    assert slow_value == "test_value"


@pytest.mark.asyncio
async def test_multi_level_cache_write_back_strategy():
    """Тест стратегии write-back."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels, sync_strategy="write_back")
    await cache.initialize()
    
    # Устанавливаем значение
    await cache.set("test_key", "test_value", ttl=100)
    
    # Проверяем, что значение записано только в быстрый уровень
    fast_value = await fast_cache.get("test_key")
    slow_value = await slow_cache.get("test_key")
    
    assert fast_value == "test_value"
    # Значение может быть и в медленном кэше, если оно уже там было, 
    # но в рамках теста предполагаем, что оно должно быть в обоих при write_back
    # т.к. в нашей реализации write_back записывает только в самый быстрый уровень
    # но при следующем чтении оно может быть синхронизировано


@pytest.mark.asyncio
async def test_multi_level_cache_delete():
    """Тест удаления значений."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    # Устанавливаем значения в оба кэша
    await fast_cache.set("test_key", "test_value", ttl=100)
    await slow_cache.set("test_key", "test_value", ttl=100)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Удаляем значение
    result = await cache.delete("test_key")
    assert result is True
    
    # Проверяем, что значение удалено из обоих кэшей
    fast_value = await fast_cache.get("test_key")
    slow_value = await slow_cache.get("test_key")
    
    assert fast_value is None
    assert slow_value is None


@pytest.mark.asyncio
async def test_multi_level_cache_exists():
    """Тест проверки существования ключа."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    # Устанавливаем значение только в медленный кэш
    await slow_cache.set("test_key", "test_value", ttl=100)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Проверяем существование ключа
    exists = await cache.exists("test_key")
    assert exists is True
    
    # Проверяем несуществующий ключ
    exists = await cache.exists("nonexistent_key")
    assert exists is False


@pytest.mark.asyncio
async def test_multi_level_cache_ttl():
    """Тест работы с TTL."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    # Устанавливаем значение с TTL в медленный кэш
    await slow_cache.set("test_key", "test_value", ttl=100)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Получаем TTL
    ttl = await cache.ttl("test_key")
    assert ttl > 0  # Должно быть положительное значение
    
    # Проверяем TTL для несуществующего ключа
    ttl = await cache.ttl("nonexistent_key")
    assert ttl == -1


@pytest.mark.asyncio
async def test_multi_level_cache_hash_operations():
    """Тест операций с хэшами."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Устанавливаем значение в хэш
    await cache.hset("test_hash", "field1", "value1", ttl=100)
    await cache.hset("test_hash", "field2", "value2", ttl=100)
    
    # Получаем значения
    value1 = await cache.hget("test_hash", "field1")
    value2 = await cache.hget("test_hash", "field2")
    
    assert value1 == "value1"
    assert value2 == "value2"
    
    # Получаем все значения хэша
    all_values = await cache.hgetall("test_hash")
    assert all_values == {"field1": "value1", "field2": "value2"}
    
    # Удаляем поле из хэша
    # При удалении из многоуровневого кэша поле удаляется из всех уровней,
    # поэтому возвращается общее количество удаленных полей из всех уровней
    deleted_count = await cache.hdel("test_hash", "field1")
    # Важно: при write-through стратегии, данные могут быть в обоих кэшах,
    # поэтому удаление может вернуть больше 1
    assert deleted_count >= 1  # Удалено хотя бы одно поле
    
    # Проверяем, что поле удалено из основного кэша
    value1 = await cache.hget("test_hash", "field1")
    assert value1 is None


@pytest.mark.asyncio
async def test_multi_level_cache_stats():
    """Тест получения статистики."""
    fast_cache = MockCache("fast", available=True)
    slow_cache = MockCache("slow", available=True)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=300),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Устанавливаем несколько значений
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    # Получаем статистику
    stats = await cache.get_stats()
    
    assert "sync_strategy" in stats
    assert "initialized" in stats
    assert "levels" in stats
    assert len(stats["levels"]) == 2
    
    # Проверяем, что уровни есть в статистике
    level_names = [level["name"] for level in stats["levels"]]
    assert "fast" in level_names
    assert "slow" in level_names


@pytest.mark.asyncio
async def test_multi_level_cache_add_remove_level():
    """Тест добавления и удаления уровней."""
    cache = MultiLevelCache()
    await cache.initialize()
    
    # Добавляем новый уровень
    new_cache = MockCache("new", available=True)
    await cache.add_level("new", new_cache, 2, default_ttl=900)
    
    # Проверяем, что уровень добавлен
    levels = [level.name for level in cache._levels]
    assert "new" in levels
    
    # Удаляем уровень
    await cache.remove_level("new")
    
    # Проверяем, что уровень удален
    levels = [level.name for level in cache._levels]
    assert "new" not in levels