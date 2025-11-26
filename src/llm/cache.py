"""
Cache Service для LLM ответов.
Кэширует ответы для экономии API запросов и ускорения работы.
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio

from .models import LLMResponse

logger = logging.getLogger(__name__)


class CacheService:
    """
    Сервис кэширования LLM ответов.
    
    Поддерживает:
    - In-memory кэш с LRU eviction
    - Redis backend (опционально)
    - TTL для записей
    - Генерация cache keys из промптов
    - Статистика cache hits/misses
    """
    
    def __init__(
        self,
        redis_client=None,
        max_memory_size: int = 1000,
        default_ttl: int = 3600
    ):
        """
        Инициализация Cache Service.
        
        Args:
            redis_client: Redis клиент (опционально)
            max_memory_size: Максимальный размер in-memory кэша
            default_ttl: TTL по умолчанию в секундах
        """
        self.redis = redis_client
        self.use_redis = redis_client is not None
        self.default_ttl = default_ttl
        
        # In-memory LRU cache
        self.max_memory_size = max_memory_size
        self._memory_cache: OrderedDict = OrderedDict()
        self._cache_lock = asyncio.Lock()
        
        # Статистика
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
        
        logger.info(f"CacheService initialized (Redis: {self.use_redis}, max_size: {max_memory_size})")
    
    async def get(self, key: str) -> Optional[LLMResponse]:
        """
        Получить значение из кэша.
        
        Args:
            key: Ключ кэша
            
        Returns:
            LLMResponse если найден, None если нет
        """
        self.total_requests += 1
        
        if self.use_redis:
            result = await self._get_redis(key)
        else:
            result = await self._get_memory(key)
        
        if result:
            self.hits += 1
            logger.debug(f"Cache HIT: {key[:50]}...")
        else:
            self.misses += 1
            logger.debug(f"Cache MISS: {key[:50]}...")
        
        return result
    
    async def set(
        self,
        key: str,
        value: LLMResponse,
        ttl: Optional[int] = None
    ):
        """
        Сохранить значение в кэш.
        
        Args:
            key: Ключ кэша
            value: LLMResponse для сохранения
            ttl: TTL в секундах (если None - используется default_ttl)
        """
        ttl = ttl or self.default_ttl
        
        # Помечаем как кэшированный
        value.cached = True
        
        if self.use_redis:
            await self._set_redis(key, value, ttl)
        else:
            await self._set_memory(key, value, ttl)
        
        logger.debug(f"Cache SET: {key[:50]}... (TTL: {ttl}s)")
    
    async def delete(self, key: str):
        """
        Удалить значение из кэша.
        
        Args:
            key: Ключ кэша
        """
        if self.use_redis:
            await self.redis.delete(key)
        else:
            async with self._cache_lock:
                if key in self._memory_cache:
                    del self._memory_cache[key]
        
        logger.debug(f"Cache DELETE: {key[:50]}...")
    
    async def clear(self):
        """Очистить весь кэш."""
        if self.use_redis:
            # Удаляем все ключи с префиксом llm_cache:
            keys = await self.redis.keys("llm_cache:*")
            if keys:
                await self.redis.delete(*keys)
        else:
            async with self._cache_lock:
                self._memory_cache.clear()
        
        logger.info("Cache cleared")
    
    def generate_key(
        self,
        provider: str,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Генерация ключа кэша из параметров запроса.
        
        Args:
            provider: Название провайдера
            model: Название модели
            prompt: Пользовательский промпт
            system_prompt: Системный промпт
            **kwargs: Дополнительные параметры
            
        Returns:
            Хэш ключ для кэша
        """
        # Создаем словарь с параметрами
        cache_data = {
            'provider': provider,
            'model': model,
            'prompt': prompt,
            'system_prompt': system_prompt,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 1000)
        }
        
        # Сериализуем в JSON и хэшируем
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()
        
        return f"llm_cache:{provider}:{cache_hash}"
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику кэша.
        
        Returns:
            Словарь со статистикой
        """
        hit_rate = (self.hits / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            'total_requests': self.total_requests,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'cache_size': len(self._memory_cache) if not self.use_redis else 'N/A',
            'max_size': self.max_memory_size if not self.use_redis else 'N/A',
            'backend': 'redis' if self.use_redis else 'memory'
        }
    
    def reset_stats(self):
        """Сбросить статистику."""
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
    
    # Redis implementation
    
    async def _get_redis(self, key: str) -> Optional[LLMResponse]:
        """Получить из Redis."""
        try:
            data = await self.redis.get(key)
            if data:
                # Десериализуем
                response_dict = json.loads(data)
                return self._dict_to_response(response_dict)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def _set_redis(self, key: str, value: LLMResponse, ttl: int):
        """Сохранить в Redis."""
        try:
            # Сериализуем
            response_dict = self._response_to_dict(value)
            data = json.dumps(response_dict)
            
            # Сохраняем с TTL
            await self.redis.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    # Memory implementation
    
    async def _get_memory(self, key: str) -> Optional[LLMResponse]:
        """Получить из памяти."""
        async with self._cache_lock:
            if key not in self._memory_cache:
                return None
            
            entry = self._memory_cache[key]
            
            # Проверяем TTL
            if datetime.now() > entry['expires_at']:
                del self._memory_cache[key]
                return None
            
            # Перемещаем в конец (LRU)
            self._memory_cache.move_to_end(key)
            
            return entry['value']
    
    async def _set_memory(self, key: str, value: LLMResponse, ttl: int):
        """Сохранить в память."""
        async with self._cache_lock:
            # LRU eviction если кэш полон
            if len(self._memory_cache) >= self.max_memory_size:
                # Удаляем самый старый элемент
                oldest_key = next(iter(self._memory_cache))
                del self._memory_cache[oldest_key]
                logger.debug(f"LRU eviction: {oldest_key[:50]}...")
            
            # Сохраняем с TTL
            self._memory_cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now()
            }
            
            # Перемещаем в конец
            self._memory_cache.move_to_end(key)
    
    # Serialization helpers
    
    @staticmethod
    def _response_to_dict(response: LLMResponse) -> dict:
        """Конвертировать LLMResponse в словарь."""
        return {
            'text': response.text,
            'provider': response.provider,
            'model': response.model,
            'tokens_used': response.tokens_used,
            'generation_time': response.generation_time,
            'cached': response.cached,
            'metadata': response.metadata,
            'timestamp': response.timestamp.isoformat()
        }
    
    @staticmethod
    def _dict_to_response(data: dict) -> LLMResponse:
        """Конвертировать словарь в LLMResponse."""
        return LLMResponse(
            text=data['text'],
            provider=data['provider'],
            model=data['model'],
            tokens_used=data['tokens_used'],
            generation_time=data['generation_time'],
            cached=data.get('cached', True),
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )
    
    async def cleanup_expired(self):
        """
        Очистка истекших записей (для in-memory режима).
        """
        if self.use_redis:
            return  # Redis сам управляет TTL
        
        async with self._cache_lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if now > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._memory_cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


class SemanticCache:
    """
    Семантический кэш для похожих промптов.
    
    Использует эмбеддинги для поиска похожих запросов.
    (Упрощенная версия - для полной реализации нужны эмбеддинги)
    """
    
    def __init__(self, cache_service: CacheService, similarity_threshold: float = 0.9):
        """
        Инициализация семантического кэша.
        
        Args:
            cache_service: Базовый cache service
            similarity_threshold: Порог схожести (0.0-1.0)
        """
        self.cache = cache_service
        self.similarity_threshold = similarity_threshold
        logger.info(f"SemanticCache initialized (threshold: {similarity_threshold})")
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Вычислить схожесть двух текстов (упрощенная версия).
        
        Args:
            text1: Первый текст
            text2: Второй текст
            
        Returns:
            Коэффициент схожести (0.0-1.0)
        """
        # Упрощенная реализация - Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def find_similar(
        self,
        prompt: str,
        provider: str,
        model: str
    ) -> Optional[LLMResponse]:
        """
        Найти похожий кэшированный ответ.
        
        Args:
            prompt: Промпт для поиска
            provider: Провайдер
            model: Модель
            
        Returns:
            LLMResponse если найден похожий, None если нет
        """
        # В упрощенной версии просто проверяем точное совпадение
        # Для полной реализации нужно хранить эмбеддинги и искать по ним
        
        key = self.cache.generate_key(provider, model, prompt)
        return await self.cache.get(key)
