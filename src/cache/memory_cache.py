"""Реализация кэша в памяти как альтернатива Redis."""

import asyncio
import logging
import time
from typing import Optional, Any, Dict, List, Union
from dataclasses import dataclass
from src.cache.i_cache import ICache
from src.cache.exceptions import CacheKeyError, CacheSerializationError

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись в кэше с временем жизни."""
    value: Any
    expiry_time: float # Время в секундах с epoch
    
    def is_expired(self) -> bool:
        """Проверить, истекло ли время жизни записи."""
        return time.time() > self.expiry_time


@dataclass
class HashEntry:
    """Запись для хэш-структуры в кэше."""
    data: Dict[str, Any]
    expiry_time: float # Время в секундах с epoch
    
    def is_expired(self) -> bool:
        """Проверить, истекло ли время жизни записи."""
        return time.time() > self.expiry_time


class MemoryCache:
    """Реализация ICache с использованием памяти."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Инициализация кэша в памяти.
        
        Args:
            max_size: Максимальный размер кэша
            default_ttl: Время жизни по умолчанию в секундах
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._hashes: Dict[str, HashEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 60 # Проверять каждую минуту
    
    async def start_cleanup_task(self):
        """Запустить фоновую задачу для очистки устаревших записей."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Остановить фоновую задачу очистки."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """Цикл очистки устаревших записей."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory cache cleanup: {e}")
    
    async def _cleanup_expired(self):
        """Очистить устаревшие записи из кэша."""
        async with self._lock:
            # Очистка основного кэша
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            # Очистка хэш-кэша
            expired_hash_keys = [
                key for key, entry in self._hashes.items()
                if entry.is_expired()
            ]
            for key in expired_hash_keys:
                del self._hashes[key]
            if expired_hash_keys:
                logger.debug(f"Cleaned up {len(expired_hash_keys)} expired hash entries")
    
    async def _evict_if_needed(self):
        """Удалить лишние записи, если превышен максимальный размер."""
        if len(self._cache) >= self._max_size:
            # Простая стратегия LRU - удалить 10% самых старых записей
            items = list(self._cache.items())
            items.sort(key=lambda x: x[1].expiry_time)  # Сортировка по времени истечения
            to_remove = max(1, self._max_size // 10)
            for key, _ in items[:to_remove]:
                del self._cache[key]
    
    def _validate_key(self, key: str) -> None:
        """Проверить валидность ключа."""
        if not isinstance(key, str):
            raise CacheKeyError(f"Key must be a string, got {type(key)}")
        if not key:
            raise CacheKeyError("Key cannot be empty")
        if len(key) > 1000:  # Ограничение длины ключа
            raise CacheKeyError(f"Key is too long: {len(key)} characters")
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша по ключу."""
        self._validate_key(key)
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    del self._cache[key]
                    return None
                return entry.value
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранить значение в кэш с опциональным временем жизни."""
        self._validate_key(key)
        async with self._lock:
            await self._evict_if_needed()
            ttl = ttl or self._default_ttl
            expiry_time = time.time() + ttl
            self._cache[key] = CacheEntry(value, expiry_time)
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша по ключу."""
        self._validate_key(key)
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа в кэше."""
        self._validate_key(key)
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    del self._cache[key]
                    return False
                return True
            return False
    
    async def clear(self) -> None:
        """Очистить весь кэш."""
        async with self._lock:
            self._cache.clear()
            self._hashes.clear()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Получить список ключей по паттерну.
        
        Note: В простой реализации поддерживает только '*' в конце паттерна.
        """
        async with self._lock:
            if pattern == "*":
                return list(self._cache.keys())
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                return [key for key in self._cache.keys() if key.startswith(prefix)]
            else:
                # Для простоты, возвращаем только точные совпадения
                return [key for key in self._cache.keys() if key == pattern]
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Получить несколько значений по списку ключей."""
        results = []
        for key in keys:
            self._validate_key(key)
            results.append(await self.get(key))
        return results
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Установить несколько пар ключ-значение."""
        for key, value in mapping.items():
            self._validate_key(key)
            await self.set(key, value, ttl)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Установить время жизни для ключа."""
        self._validate_key(key)
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    entry.expiry_time = time.time() + ttl
                    return True
            return False
    
    async def ttl(self, key: str) -> int:
        """Получить оставшееся время жизни ключа."""
        self._validate_key(key)
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    remaining = int(entry.expiry_time - time.time())
                    return max(0, remaining)
            return -1  # Ключ не существует или истек
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Получить значение из хэша по ключу."""
        self._validate_key(name)
        self._validate_key(key)
        async with self._lock:
            if name in self._hashes:
                hash_entry = self._hashes[name]
                if hash_entry.is_expired():
                    del self._hashes[name]
                    return None
                return hash_entry.data.get(key)
            return None
    
    async def hset(self, name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установить значение в хэш."""
        self._validate_key(name)
        self._validate_key(key)
        async with self._lock:
            ttl = ttl or self._default_ttl
            expiry_time = time.time() + ttl
            
            if name in self._hashes:
                hash_entry = self._hashes[name]
                if hash_entry.is_expired():
                    del self._hashes[name]
                else:
                    hash_entry.data[key] = value
                    hash_entry.expiry_time = expiry_time
                    return
            
            # Создать новый хэш, если его не существует или он истек
            self._hashes[name] = HashEntry({key: value}, expiry_time)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Удалить один или несколько ключей из хэша."""
        self._validate_key(name)
        for key in keys:
            self._validate_key(key)
        
        deleted_count = 0
        async with self._lock:
            if name in self._hashes:
                hash_entry = self._hashes[name]
                if not hash_entry.is_expired():
                    for key in keys:
                        if key in hash_entry.data:
                            del hash_entry.data[key]
                            deleted_count += 1
                    # Если хэш стал пустым, удалить его
                    if not hash_entry.data:
                        del self._hashes[name]
        
        return deleted_count
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Получить все поля и значения из хэша."""
        self._validate_key(name)
        async with self._lock:
            if name in self._hashes:
                hash_entry = self._hashes[name]
                if hash_entry.is_expired():
                    del self._hashes[name]
                    return {}
                return hash_entry.data.copy()
            return {}
    
    async def ping(self) -> bool:
        """Проверить доступность кэш-сервера."""
        return True  # Всегда доступен
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику использования кэша."""
        async with self._lock:
            return {
                'total_keys': len(self._cache),
                'total_hashes': len(self._hashes),
                'max_size': self._max_size,
                'current_size': len(self._cache),
                'current_hash_size': len(self._hashes)
            }
    
    async def close(self) -> None:
        """Закрыть соединение с кэш-сервером."""
        await self.stop_cleanup_task()
        async with self._lock:
            self._cache.clear()
            self._hashes.clear()