"""Cache module with Redis and memory fallback support."""

import asyncio
import logging
from typing import Optional
from src.cache.multi_level_cache import MultiLevelCache

logger = logging.getLogger(__name__)

# Global cache instance
cache: Optional[MultiLevelCache] = None

# Инициализировать кэш при импорте
async def _initialize_cache():
    """Асинхронная инициализация глобального кэша."""
    global cache
    cache = MultiLevelCache()
    try:
        await cache.initialize()
        logger.info("Global cache initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize global cache: {e}")
        # В случае ошибки инициализации создаем кэш без подключения к Redis
        cache = MultiLevelCache()
        try:
            await cache._memory_cache.start_cleanup_task()
            logger.warning("Global cache initialized in memory-only mode")
        except Exception as e:
            logger.error(f"Failed to initialize memory cache: {e}")

# Попробовать инициализировать кэш
try:
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        loop.run_until_complete(_initialize_cache())
    else:
        # Если event loop уже запущен, создаем задачу
        asyncio.create_task(_initialize_cache())
except RuntimeError:
    # Если нет event loop, создаем новый
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_initialize_cache())

async def get_cache() -> MultiLevelCache:
    """Получить экземпляр глобального кэша."""
    global cache
    if cache is None:
        # Попробовать инициализировать кэш, если он не был инициализирован при импорте
        await _initialize_cache()
    return cache

__all__ = ['cache', 'MultiLevelCache', 'get_cache']