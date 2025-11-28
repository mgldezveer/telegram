"""Реализация кэша с использованием Redis."""

import json
import logging
from typing import Optional, Any, List, Dict, Union
from src.cache.i_cache import ICache
from src.config import config
from src.cache.redis_config import RedisConfig
from src.cache.exceptions import CacheBackendError, CacheSerializationError, CacheConnectionError

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis library not available, using memory cache only")


class RedisCache:
    """Реализация ICache с использованием Redis."""
    
    def __init__(self, url: Optional[str] = None, default_ttl: int = 300, redis_config: Optional[RedisConfig] = None):
        """Инициализация Redis кэша.
        
        Args:
            url: URL подключения к Redis (если None, используется из конфига)
            default_ttl: Время жизни по умолчанию в секундах
            redis_config: Экземпляр RedisConfig (если None, используется из глобального конфига)
        """
        # Если передан redis_config, используем его, иначе создаем из глобального конфига
        if redis_config is None:
            # Создаем экземпляр RedisConfig из основного конфига
            self._config = RedisConfig(
                url=url or config.redis.url,
                max_connections=config.redis.max_connections
            )
        else:
            self._config = redis_config
            
        self.url = self._config.url
        self.default_ttl = default_ttl
        self._client: Optional[Redis] = None
        self._connected = False
        self._connection_params = self._config.get_connection_params()
    
    async def connect(self) -> bool:
        """Подключиться к Redis."""
        if not REDIS_AVAILABLE:
            logger.error("Redis library not available")
            raise CacheBackendError("Redis library not available")
            
        try:
            self._client = redis.from_url(
                self.url,
                **self._connection_params
            )
            # Проверка подключения
            await self._client.ping()
            self._connected = True
            logger.info("Connected to Redis successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise CacheConnectionError(f"Failed to connect to Redis: {e}")
    
    async def ensure_connection(self) -> bool:
        """Убедиться, что подключение к Redis установлено."""
        if not self._connected or self._client is None:
            return await self.connect()
        return True
    
    def _serialize(self, value: Any) -> str:
        """Сериализовать значение для хранения в Redis."""
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception as e:
            raise CacheSerializationError(f"Failed to serialize value: {e}")
    
    def _deserialize(self, value: str) -> Any:
        """Десериализовать значение из Redis."""
        try:
            return json.loads(value)
        except Exception as e:
            raise CacheSerializationError(f"Failed to deserialize value: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша по ключу."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            value = await self._client.get(key)
            if value is not None:
                return self._deserialize(value)
            return None
        except Exception as e:
            logger.error(f"Error getting value from Redis cache for key {key}: {e}")
            raise CacheBackendError(f"Error getting value from Redis cache for key {key}: {e}")
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранить значение в кэш с опциональным временем жизни."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            ttl = ttl or self.default_ttl
            serialized = self._serialize(value)
            await self._client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Error setting value to Redis cache for key {key}: {e}")
            raise CacheBackendError(f"Error setting value to Redis cache for key {key}: {e}")
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша по ключу."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key from Redis cache {key}: {e}")
            raise CacheBackendError(f"Error deleting key from Redis cache {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа в кэше."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking existence of key in Redis cache {key}: {e}")
            raise CacheBackendError(f"Error checking existence of key in Redis cache {key}: {e}")
    
    async def clear(self) -> None:
        """Очистить весь кэш."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            await self._client.flushdb()
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            raise CacheBackendError(f"Error clearing Redis cache: {e}")
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Получить список ключей по паттерну."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            return await self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting keys from Redis cache with pattern {pattern}: {e}")
            raise CacheBackendError(f"Error getting keys from Redis cache with pattern {pattern}: {e}")
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Получить несколько значений по списку ключей."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            values = await self._client.mget(keys)
            result = []
            for value in values:
                if value is not None:
                    result.append(self._deserialize(value))
                else:
                    result.append(None)
            return result
        except Exception as e:
            logger.error(f"Error getting multiple values from Redis cache: {e}")
            raise CacheBackendError(f"Error getting multiple values from Redis cache: {e}")
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Установить несколько пар ключ-значение."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            serialized_mapping = {}
            for key, value in mapping.items():
                serialized_mapping[key] = self._serialize(value)
            
            await self._client.mset(serialized_mapping)
            
            # Установить TTL для всех ключей, если указан
            if ttl is not None:
                for key in mapping.keys():
                    await self._client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Error setting multiple values to Redis cache: {e}")
            raise CacheBackendError(f"Error setting multiple values to Redis cache: {e}")
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Установить время жизни для ключа."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            result = await self._client.expire(key, ttl)
            return result
        except Exception as e:
            logger.error(f"Error setting TTL for key in Redis cache {key}: {e}")
            raise CacheBackendError(f"Error setting TTL for key in Redis cache {key}: {e}")
    
    async def ttl(self, key: str) -> int:
        """Получить оставшееся время жизни ключа."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key in Redis cache {key}: {e}")
            raise CacheBackendError(f"Error getting TTL for key in Redis cache {key}: {e}")
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Получить значение из хэша по ключу."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            value = await self._client.hget(name, key)
            if value is not None:
                return self._deserialize(value)
            return None
        except Exception as e:
            logger.error(f"Error getting hash value from Redis cache for key {key} in hash {name}: {e}")
            raise CacheBackendError(f"Error getting hash value from Redis cache for key {key} in hash {name}: {e}")
    
    async def hset(self, name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установить значение в хэш."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            serialized = self._serialize(value)
            await self._client.hset(name, key, serialized)
            
            # Установить TTL для всего хэша, если указан
            if ttl is not None:
                await self._client.expire(name, ttl)
        except Exception as e:
            logger.error(f"Error setting hash value to Redis cache for key {key} in hash {name}: {e}")
            raise CacheBackendError(f"Error setting hash value to Redis cache for key {key} in hash {name}: {e}")
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Удалить один или несколько ключей из хэша."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            result = await self._client.hdel(name, *keys)
            return result
        except Exception as e:
            logger.error(f"Error deleting keys from Redis hash {name}: {e}")
            raise CacheBackendError(f"Error deleting keys from Redis hash {name}: {e}")
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Получить все поля и значения из хэша."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            values = await self._client.hgetall(name)
            result = {}
            for key, value in values.items():
                result[key] = self._deserialize(value)
            return result
        except Exception as e:
            logger.error(f"Error getting all values from Redis hash {name}: {e}")
            raise CacheBackendError(f"Error getting all values from Redis hash {name}: {e}")
    
    async def ping(self) -> bool:
        """Проверить доступность кэш-сервера."""
        try:
            if not await self.ensure_connection():
                return False
            await self._client.ping()
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику использования кэша."""
        if not await self.ensure_connection():
            raise CacheBackendError("Redis is not connected")
            
        try:
            info = await self._client.info()
            return {
                'connected': self._connected,
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1)
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            raise CacheBackendError(f"Error getting Redis stats: {e}")
    
    async def close(self) -> None:
        """Закрыть соединение с Redis."""
        if self._client:
            await self._client.close()
            self._connected = False