"""Мультиуровневый кэш с поддержкой Redis и памяти."""

import logging
from typing import Optional, Any, List, Dict, Union, Callable, Tuple
from src.cache.i_cache import ICache
from src.cache.redis_cache import RedisCache
from src.cache.memory_cache import MemoryCache
from src.cache.exceptions import CacheBackendError

logger = logging.getLogger(__name__)


class CacheLevel:
    """Представление уровня кэша."""
    
    def __init__(self, name: str, cache_instance: ICache, priority: int, default_ttl: Optional[int] = None):
        """
        Args:
            name: Название уровня кэша
            cache_instance: Экземпляр кэша
            priority: Приоритет уровня (меньше число - выше приоритет)
            default_ttl: Время жизни по умолчанию для уровня
        """
        self.name = name
        self.cache = cache_instance
        self.priority = priority
        self.default_ttl = default_ttl
        self.available = True  # Доступен ли уровень кэша


class MultiLevelCache:
    """Мультиуровневая реализация кэша с поддержкой Redis, памяти и других бэкендов."""
    
    def __init__(self, levels: Optional[List[CacheLevel]] = None, sync_strategy: str = "write_through"):
        """Инициализация мультиуровневого кэша.
        
        Args:
            levels: Список уровней кэша. Если None, создается стандартный набор (Redis -> Memory).
            sync_strategy: Стратегия синхронизации между уровнями ("write_through", "write_back", "write_around")
        """
        if levels is None:
            # Создаем стандартные уровни: Redis (приоритет 0) -> Memory (приоритет 1)
            self._levels = [
                CacheLevel("redis", RedisCache(), 0),
                CacheLevel("memory", MemoryCache(), 1)
            ]
        else:
            # Сортируем уровни по приоритету
            self._levels = sorted(levels, key=lambda x: x.priority)
        
        self._sync_strategy = sync_strategy
        self._initialized = False
    
    async def initialize(self):
        """Инициализировать все уровни кэша."""
        # Попытаться подключиться к Redis
        redis_level = next((level for level in self._levels if level.name == "redis"), None)
        if redis_level:
            try:
                redis_connected = await redis_level.cache.connect()
                redis_level.available = redis_connected
                if redis_connected:
                    logger.info("MultiLevelCache: Redis connected, using as primary cache")
                else:
                    logger.warning("MultiLevelCache: Redis unavailable, using memory cache only")
            except Exception as e:
                logger.error(f"MultiLevelCache: Failed to connect to Redis: {e}")
                redis_level.available = False
        
        # Запустить задачу очистки для кэша в памяти
        memory_level = next((level for level in self._levels if level.name == "memory"), None)
        if memory_level:
            await memory_level.cache.start_cleanup_task()
        
        self._initialized = True
    
    async def close(self):
        """Закрыть все уровни кэша."""
        for level in self._levels:
            try:
                await level.cache.close()
            except Exception as e:
                logger.error(f"Error closing {level.name} cache: {e}")
    
    async def _get_available_levels(self) -> List[CacheLevel]:
        """Получить список доступных уровней кэша."""
        return [level for level in self._levels if level.available]
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша по ключу.
        
        Сначала проверяются уровни с более высоким приоритетом (меньше число приоритета).
        Если значение найдено в более медленном уровне, оно записывается в более быстрые уровни.
        """
        available_levels = await self._get_available_levels()
        
        # Пробуем получить значение из каждого уровня порядку приоритета
        result = None
        found_at_level = -1
        
        for i, level in enumerate(available_levels):
            try:
                result = await level.cache.get(key)
                if result is not None:
                    found_at_level = i
                    break
            except CacheBackendError as e:
                logger.warning(f"Cache level {level.name} unavailable: {e}")
                level.available = False
        
        # Если значение найдено не в самом быстром уровне, записываем его туда для ускорения доступа
        if result is not None and found_at_level > 0:
            # Записываем значение во все более быстрые уровни
            for i in range(found_at_level):
                try:
                    fast_level = available_levels[i]
                    ttl = fast_level.default_ttl
                    await fast_level.cache.set(key, result, ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to write to cache level {available_levels[i].name}: {e}")
        
        return result
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранить значение в кэш с опциональным временем жизни.
        
        В зависимости от стратегии синхронизации, записывает в один или несколько уровней.
        """
        available_levels = await self._get_available_levels()
        
        if self._sync_strategy == "write_through":
            # Записываем во все уровни сразу
            for level in available_levels:
                try:
                    level_ttl = ttl or level.default_ttl
                    await level.cache.set(key, value, level_ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to write to cache level {level.name}: {e}")
                    level.available = False
        elif self._sync_strategy == "write_back":
            # Записываем только в самый быстрый уровень, а остальные обновляются позже
            if available_levels:
                try:
                    fastest_level = available_levels[0]  # Самый быстрый уровень
                    level_ttl = ttl or fastest_level.default_ttl
                    await fastest_level.cache.set(key, value, level_ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to write to cache level {available_levels[0].name}: {e}")
                    available_levels[0].available = False
        elif self._sync_strategy == "write_around":
            # Записываем только в самый медленный уровень (обычно в основное хранилище)
            if available_levels:
                try:
                    slowest_level = available_levels[-1]  # Самый медленный уровень
                    level_ttl = ttl or slowest_level.default_ttl
                    await slowest_level.cache.set(key, value, level_ttl)
                    
                    # Удаляем из более быстрых уровней, чтобы избежать несогласованности
                    for level in available_levels[:-1]:
                        try:
                            await level.cache.delete(key)
                        except CacheBackendError:
                            pass  # Не критично, если не удалось удалить
                except CacheBackendError as e:
                    logger.warning(f"Failed to write to cache level {available_levels[-1].name}: {e}")
                    available_levels[-1].available = False
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша по ключу.
        
        Удаляет из всех уровней кэша.
        """
        result = False
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                level_result = await level.cache.delete(key)
                result = result or level_result
            except CacheBackendError as e:
                logger.warning(f"Failed to delete from cache level {level.name}: {e}")
                level.available = False
        
        return result
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа в кэше.
        
        Проверяет в уровнях по порядку приоритета.
        """
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                if await level.cache.exists(key):
                    return True
            except CacheBackendError as e:
                logger.warning(f"Failed to check existence in cache level {level.name}: {e}")
                level.available = False
        
        return False
    
    async def clear(self) -> None:
        """Очистить весь кэш."""
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                await level.cache.clear()
            except CacheBackendError as e:
                logger.warning(f"Failed to clear cache level {level.name}: {e}")
                level.available = False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Получить список ключей по паттерну.
        
        Возвращает объединение ключей из всех уровней.
        """
        all_keys = set()
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                level_keys = await level.cache.keys(pattern)
                all_keys.update(level_keys)
            except CacheBackendError as e:
                logger.warning(f"Failed to get keys from cache level {level.name}: {e}")
                level.available = False
        
        return list(all_keys)
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Получить несколько значений по списку ключей."""
        if not keys:
            return []
        
        available_levels = await self._get_available_levels()
        results = [None] * len(keys)
        remaining_keys = list(keys)
        remaining_indices = list(range(len(keys)))
        
        # Пробуем получить значения из каждого уровня
        for level in available_levels:
            if not remaining_keys:
                break
            
            try:
                level_values = await level.cache.mget(remaining_keys)
                
                # Обновляем результаты и определяем, какие ключи были найдены
                next_remaining_keys = []
                next_remaining_indices = []
                
                for i, (key_idx, key) in enumerate(zip(remaining_indices, remaining_keys)):
                    if level_values[i] is not None:
                        results[key_idx] = level_values[i]
                        # Записываем найденное значение в более быстрые уровни
                        if level.priority > 0:  # Не самый быстрый уровень
                            for faster_level in available_levels[:level.priority]:
                                try:
                                    ttl = faster_level.default_ttl
                                    await faster_level.cache.set(key, level_values[i], ttl)
                                except CacheBackendError:
                                    pass  # Не критично, если не удалось записать
                    else:
                        # Ключ не найден в этом уровне, сохраняем для следующих уровней
                        next_remaining_keys.append(key)
                        next_remaining_indices.append(key_idx)
                
                remaining_keys = next_remaining_keys
                remaining_indices = next_remaining_indices
                
            except CacheBackendError as e:
                logger.warning(f"Failed to mget from cache level {level.name}: {e}")
                level.available = False
        
        return results
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Установить несколько пар ключ-значение."""
        if not mapping:
            return
        
        available_levels = await self._get_available_levels()
        
        if self._sync_strategy == "write_through":
            # Записываем во все уровни сразу
            for level in available_levels:
                try:
                    level_ttl = ttl or level.default_ttl
                    await level.cache.mset(mapping, level_ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to mset to cache level {level.name}: {e}")
                    level.available = False
        elif self._sync_strategy == "write_back":
            # Записываем только в самый быстрый уровень
            if available_levels:
                try:
                    fastest_level = available_levels[0]
                    level_ttl = ttl or fastest_level.default_ttl
                    await fastest_level.cache.mset(mapping, level_ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to mset to cache level {available_levels[0].name}: {e}")
                    available_levels[0].available = False
        elif self._sync_strategy == "write_around":
            # Записываем только в самый медленный уровень
            if available_levels:
                try:
                    slowest_level = available_levels[-1]
                    level_ttl = ttl or slowest_level.default_ttl
                    await slowest_level.cache.mset(mapping, level_ttl)
                    
                    # Удаляем из более быстрых уровней
                    for level in available_levels[:-1]:
                        try:
                            for key in mapping.keys():
                                await level.cache.delete(key)
                        except CacheBackendError:
                            pass
                except CacheBackendError as e:
                    logger.warning(f"Failed to mset to cache level {available_levels[-1].name}: {e}")
                    available_levels[-1].available = False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Установить время жизни для ключа."""
        result = False
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                level_result = await level.cache.expire(key, ttl)
                result = result or level_result
            except CacheBackendError as e:
                logger.warning(f"Failed to set expire for cache level {level.name}: {e}")
                level.available = False
        
        return result
    
    async def ttl(self, key: str) -> int:
        """Получить оставшееся время жизни ключа.
        
        Возвращает TTL из самого быстрого уровня, где ключ найден.
        """
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                level_ttl = await level.cache.ttl(key)
                if level_ttl != -1:
                    return level_ttl
            except CacheBackendError as e:
                logger.warning(f"Failed to get TTL from cache level {level.name}: {e}")
                level.available = False
        
        return -1  # Ключ не найден ни в одном уровне
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Получить значение из хэша по ключу."""
        available_levels = await self._get_available_levels()
        
        result = None
        found_at_level = -1
        
        for i, level in enumerate(available_levels):
            try:
                result = await level.cache.hget(name, key)
                if result is not None:
                    found_at_level = i
                    break
            except CacheBackendError as e:
                logger.warning(f"Failed to hget from cache level {level.name}: {e}")
                level.available = False
        
        # Если значение найдено не в самом быстром уровне, записываем его туда
        if result is not None and found_at_level > 0:
            for i in range(found_at_level):
                try:
                    fast_level = available_levels[i]
                    ttl = fast_level.default_ttl
                    await fast_level.cache.hset(name, key, result, ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to write to cache level {available_levels[i].name}: {e}")
        
        return result
    
    async def hset(self, name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установить значение в хэш."""
        available_levels = await self._get_available_levels()
        
        if self._sync_strategy == "write_through":
            # Записываем во все уровни
            for level in available_levels:
                try:
                    level_ttl = ttl or level.default_ttl
                    await level.cache.hset(name, key, value, level_ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to hset to cache level {level.name}: {e}")
                    level.available = False
        elif self._sync_strategy == "write_back":
            # Записываем только в самый быстрый уровень
            if available_levels:
                try:
                    fastest_level = available_levels[0]
                    level_ttl = ttl or fastest_level.default_ttl
                    await fastest_level.cache.hset(name, key, value, level_ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to hset to cache level {available_levels[0].name}: {e}")
                    available_levels[0].available = False
        elif self._sync_strategy == "write_around":
            # Записываем только в самый медленный уровень
            if available_levels:
                try:
                    slowest_level = available_levels[-1]
                    level_ttl = ttl or slowest_level.default_ttl
                    await slowest_level.cache.hset(name, key, value, level_ttl)
                    
                    # Удаляем из более быстрых уровней
                    for level in available_levels[:-1]:
                        try:
                            await level.cache.hdel(name, key)
                        except CacheBackendError:
                            pass
                except CacheBackendError as e:
                    logger.warning(f"Failed to hset to cache level {available_levels[-1].name}: {e}")
                    available_levels[-1].available = False
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Удалить один или несколько ключей из хэша."""
        total_deleted = 0
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                deleted = await level.cache.hdel(name, *keys)
                total_deleted += deleted
            except CacheBackendError as e:
                logger.warning(f"Failed to hdel from cache level {level.name}: {e}")
                level.available = False
        
        return total_deleted
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Получить все поля и значения из хэша."""
        available_levels = await self._get_available_levels()
        
        result = {}
        found_at_level = -1
        
        # Пробуем получить хэш из каждого уровня
        for i, level in enumerate(available_levels):
            try:
                level_result = await level.cache.hgetall(name)
                if level_result:
                    result = level_result
                    found_at_level = i
                    break
            except CacheBackendError as e:
                logger.warning(f"Failed to hgetall from cache level {level.name}: {e}")
                level.available = False
        
        # Если найдено не в самом быстром уровне, записываем в более быстрые уровни
        if result and found_at_level > 0:
            for i in range(found_at_level):
                try:
                    fast_level = available_levels[i]
                    ttl = fast_level.default_ttl
                    for k, v in result.items():
                        await fast_level.cache.hset(name, k, v, ttl)
                except CacheBackendError as e:
                    logger.warning(f"Failed to write to cache level {available_levels[i].name}: {e}")
        
        return result
    
    async def ping(self) -> bool:
        """Проверить доступность кэш-сервера.
        
        Возвращает True, если хотя бы один уровень доступен.
        """
        available_levels = await self._get_available_levels()
        
        for level in available_levels:
            try:
                if await level.cache.ping():
                    return True
            except CacheBackendError as e:
                logger.warning(f"Failed to ping cache level {level.name}: {e}")
                level.available = False
        
        return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику использования кэша."""
        stats = {
            'sync_strategy': self._sync_strategy,
            'initialized': self._initialized,
            'levels': []
        }
        
        for level in self._levels:
            level_stats = {
                'name': level.name,
                'priority': level.priority,
                'available': level.available,
                'default_ttl': level.default_ttl
            }
            
            try:
                backend_stats = await level.cache.get_stats()
                level_stats['backend_stats'] = backend_stats
            except CacheBackendError as e:
                logger.warning(f"Failed to get stats from cache level {level.name}: {e}")
                level.available = False
                level_stats['backend_stats'] = {}
            
            stats['levels'].append(level_stats)
        
        return stats
    
    def get_level_status(self) -> Dict[str, bool]:
        """Получить статус доступности каждого уровня кэша."""
        return {level.name: level.available for level in self._levels}
    
    async def add_level(self, name: str, cache_instance: ICache, priority: int, default_ttl: Optional[int] = None):
        """Добавить новый уровень кэша."""
        new_level = CacheLevel(name, cache_instance, priority, default_ttl)
        self._levels.append(new_level)
        self._levels = sorted(self._levels, key=lambda x: x.priority)
    
    async def remove_level(self, name: str):
        """Удалить уровень кэша по имени."""
        self._levels = [level for level in self._levels if level.name != name]
    
    def is_level_available(self, name: str) -> bool:
        """Проверить, доступен ли уровень кэша с указанным именем."""
        level = next((level for level in self._levels if level.name == name), None)
        return level.available if level else False