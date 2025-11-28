"""Интерфейс для кэширования с поддержкой нескольких бэкендов."""

from abc import ABC, abstractmethod
from typing import Optional, Any, Protocol, Dict, List, Union, Callable, Awaitable


class ICache(Protocol):
    """Протокол кэш-сервиса для поддержки различных бэкендов."""
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша по ключу."""
        ...
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранить значение в кэш с опциональным временем жизни."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша по ключу."""
        ...
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа в кэше."""
        ...
    
    async def clear(self) -> None:
        """Очистить весь кэш."""
        ...
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Получить список ключей по паттерну."""
        ...
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Получить несколько значений по списку ключей."""
        ...
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Установить несколько пар ключ-значение."""
        ...
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Установить время жизни для ключа."""
        ...
    
    async def ttl(self, key: str) -> int:
        """Получить оставшееся время жизни ключа."""
        ...
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Получить значение из хэша по ключу."""
        ...
    
    async def hset(self, name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установить значение в хэш."""
        ...
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Удалить один или несколько ключей из хэша."""
        ...
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Получить все поля и значения из хэша."""
        ...
    
    async def ping(self) -> bool:
        """Проверить доступность кэш-сервера."""
        ...
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику использования кэша."""
        ...
    
    async def close(self) -> None:
        """Закрыть соединение с кэш-сервером."""
        ...