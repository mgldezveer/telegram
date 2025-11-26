"""
Rate Limit Manager для LLM провайдеров.
Использует sliding window algorithm для точного контроля лимитов.
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque
import time

logger = logging.getLogger(__name__)


class RateLimitManager:
    """
    Менеджер rate limiting с поддержкой sliding window algorithm.
    
    Поддерживает:
    - Лимиты по минутам, часам и дням
    - Sliding window для точного контроля
    - In-memory хранилище (Redis опционально)
    - Автоматический reset счетчиков
    - Статистика использования
    """
    
    def __init__(self, redis_client=None):
        """
        Инициализация Rate Limit Manager.
        
        Args:
            redis_client: Redis клиент (опционально, если None - используется in-memory)
        """
        self.redis = redis_client
        self.use_redis = redis_client is not None
        
        # In-memory хранилище (fallback если нет Redis)
        self._memory_store: Dict[str, deque] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        
        logger.info(f"RateLimitManager initialized (Redis: {self.use_redis})")
    
    async def check_limit(
        self,
        provider: str,
        limit_type: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Проверка rate limit для провайдера.
        
        Args:
            provider: Название провайдера
            limit_type: Тип лимита (minute/hour/day)
            max_requests: Максимальное количество запросов
            window_seconds: Размер окна в секундах
            
        Returns:
            True если запрос можно выполнить, False если лимит превышен
        """
        key = f"rate_limit:{provider}:{limit_type}"
        
        if self.use_redis:
            return await self._check_limit_redis(key, max_requests, window_seconds)
        else:
            return await self._check_limit_memory(key, max_requests, window_seconds)
    
    async def record_request(
        self,
        provider: str,
        limit_type: str,
        window_seconds: int
    ):
        """
        Записать выполненный запрос.
        
        Args:
            provider: Название провайдера
            limit_type: Тип лимита
            window_seconds: Размер окна в секундах
        """
        key = f"rate_limit:{provider}:{limit_type}"
        
        if self.use_redis:
            await self._record_request_redis(key, window_seconds)
        else:
            await self._record_request_memory(key, window_seconds)
    
    async def get_remaining(
        self,
        provider: str,
        limit_type: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """
        Получить количество оставшихся запросов.
        
        Args:
            provider: Название провайдера
            limit_type: Тип лимита
            max_requests: Максимальное количество запросов
            window_seconds: Размер окна в секундах
            
        Returns:
            Количество оставшихся запросов
        """
        key = f"rate_limit:{provider}:{limit_type}"
        
        if self.use_redis:
            current = await self._get_current_count_redis(key, window_seconds)
        else:
            current = await self._get_current_count_memory(key, window_seconds)
        
        remaining = max(0, max_requests - current)
        return remaining
    
    async def reset(self, provider: str, limit_type: Optional[str] = None):
        """
        Сбросить счетчики для провайдера.
        
        Args:
            provider: Название провайдера
            limit_type: Тип лимита (если None - сбросить все)
        """
        if limit_type:
            key = f"rate_limit:{provider}:{limit_type}"
            if self.use_redis:
                await self.redis.delete(key)
            else:
                if key in self._memory_store:
                    del self._memory_store[key]
        else:
            # Сбросить все лимиты провайдера
            pattern = f"rate_limit:{provider}:*"
            if self.use_redis:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            else:
                keys_to_delete = [k for k in self._memory_store.keys() if k.startswith(f"rate_limit:{provider}:")]
                for key in keys_to_delete:
                    del self._memory_store[key]
        
        logger.info(f"Reset rate limits for {provider}" + (f":{limit_type}" if limit_type else ""))
    
    async def get_stats(self, provider: str) -> Dict[str, int]:
        """
        Получить статистику использования провайдера.
        
        Args:
            provider: Название провайдера
            
        Returns:
            Словарь со статистикой по каждому типу лимита
        """
        stats = {}
        
        for limit_type in ['minute', 'hour', 'day']:
            key = f"rate_limit:{provider}:{limit_type}"
            
            if self.use_redis:
                count = await self._get_current_count_redis(key, self._get_window_seconds(limit_type))
            else:
                count = await self._get_current_count_memory(key, self._get_window_seconds(limit_type))
            
            stats[limit_type] = count
        
        return stats
    
    # Redis implementation
    
    async def _check_limit_redis(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Проверка лимита через Redis."""
        try:
            current_count = await self._get_current_count_redis(key, window_seconds)
            return current_count < max_requests
        except Exception as e:
            logger.error(f"Redis check_limit error: {e}")
            # Fallback to memory
            return await self._check_limit_memory(key, max_requests, window_seconds)
    
    async def _record_request_redis(self, key: str, window_seconds: int):
        """Запись запроса через Redis."""
        try:
            now = time.time()
            
            # Добавляем timestamp в sorted set
            await self.redis.zadd(key, {str(now): now})
            
            # Удаляем старые записи
            cutoff = now - window_seconds
            await self.redis.zremrangebyscore(key, '-inf', cutoff)
            
            # Устанавливаем TTL
            await self.redis.expire(key, window_seconds)
            
        except Exception as e:
            logger.error(f"Redis record_request error: {e}")
            # Fallback to memory
            await self._record_request_memory(key, window_seconds)
    
    async def _get_current_count_redis(self, key: str, window_seconds: int) -> int:
        """Получение текущего количества запросов через Redis."""
        try:
            now = time.time()
            cutoff = now - window_seconds
            
            # Подсчитываем записи в окне
            count = await self.redis.zcount(key, cutoff, '+inf')
            return count
            
        except Exception as e:
            logger.error(f"Redis get_current_count error: {e}")
            return 0
    
    # In-memory implementation
    
    async def _check_limit_memory(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Проверка лимита через memory."""
        async with self._get_lock(key):
            current_count = await self._get_current_count_memory(key, window_seconds)
            return current_count < max_requests
    
    async def _record_request_memory(self, key: str, window_seconds: int):
        """Запись запроса через memory."""
        async with self._get_lock(key):
            now = time.time()
            
            if key not in self._memory_store:
                self._memory_store[key] = deque()
            
            # Добавляем timestamp
            self._memory_store[key].append(now)
            
            # Удаляем старые записи
            cutoff = now - window_seconds
            while self._memory_store[key] and self._memory_store[key][0] < cutoff:
                self._memory_store[key].popleft()
    
    async def _get_current_count_memory(self, key: str, window_seconds: int) -> int:
        """Получение текущего количества запросов через memory."""
        if key not in self._memory_store:
            return 0
        
        now = time.time()
        cutoff = now - window_seconds
        
        # Очищаем старые записи
        while self._memory_store[key] and self._memory_store[key][0] < cutoff:
            self._memory_store[key].popleft()
        
        return len(self._memory_store[key])
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """Получить lock для ключа."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    @staticmethod
    def _get_window_seconds(limit_type: str) -> int:
        """Получить размер окна в секундах для типа лимита."""
        windows = {
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        return windows.get(limit_type, 60)
    
    async def cleanup_old_data(self, max_age_seconds: int = 86400):
        """
        Очистка старых данных (для in-memory режима).
        
        Args:
            max_age_seconds: Максимальный возраст данных в секундах
        """
        if self.use_redis:
            return  # Redis сам управляет TTL
        
        now = time.time()
        cutoff = now - max_age_seconds
        
        keys_to_delete = []
        for key, timestamps in self._memory_store.items():
            # Удаляем старые записи
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            
            # Если очередь пустая, удаляем ключ
            if not timestamps:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._memory_store[key]
            if key in self._locks:
                del self._locks[key]
        
        if keys_to_delete:
            logger.info(f"Cleaned up {len(keys_to_delete)} old rate limit keys")


class ProviderRateLimiter:
    """
    Обертка для удобной работы с rate limiting конкретного провайдера.
    """
    
    def __init__(
        self,
        manager: RateLimitManager,
        provider: str,
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None
    ):
        """
        Инициализация rate limiter для провайдера.
        
        Args:
            manager: RateLimitManager
            provider: Название провайдера
            requests_per_minute: Лимит запросов в минуту
            requests_per_hour: Лимит запросов в час
            requests_per_day: Лимит запросов в день
        """
        self.manager = manager
        self.provider = provider
        self.limits = {
            'minute': (requests_per_minute, 60) if requests_per_minute else None,
            'hour': (requests_per_hour, 3600) if requests_per_hour else None,
            'day': (requests_per_day, 86400) if requests_per_day else None
        }
    
    async def check_all_limits(self) -> bool:
        """
        Проверить все лимиты провайдера.
        
        Returns:
            True если все лимиты позволяют запрос
        """
        for limit_type, limit_config in self.limits.items():
            if limit_config is None:
                continue
            
            max_requests, window_seconds = limit_config
            
            if not await self.manager.check_limit(
                self.provider,
                limit_type,
                max_requests,
                window_seconds
            ):
                logger.warning(f"{self.provider} rate limit exceeded: {limit_type}")
                return False
        
        return True
    
    async def record_request(self):
        """Записать выполненный запрос для всех лимитов."""
        for limit_type, limit_config in self.limits.items():
            if limit_config is None:
                continue
            
            _, window_seconds = limit_config
            await self.manager.record_request(
                self.provider,
                limit_type,
                window_seconds
            )
    
    async def get_remaining_all(self) -> Dict[str, int]:
        """
        Получить оставшиеся запросы для всех лимитов.
        
        Returns:
            Словарь с оставшимися запросами по каждому типу
        """
        remaining = {}
        
        for limit_type, limit_config in self.limits.items():
            if limit_config is None:
                remaining[limit_type] = float('inf')
                continue
            
            max_requests, window_seconds = limit_config
            remaining[limit_type] = await self.manager.get_remaining(
                self.provider,
                limit_type,
                max_requests,
                window_seconds
            )
        
        return remaining
    
    async def reset(self):
        """Сбросить все лимиты провайдера."""
        await self.manager.reset(self.provider)
