"""Пример использования многоуровневого кэша."""

import asyncio
import time
import sys
import os

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cache.multi_level_cache import MultiLevelCache, CacheLevel
from src.cache.memory_cache import MemoryCache
from src.cache.redis_cache import RedisCache


async def example_basic_usage():
    """Пример базового использования многоуровневого кэша."""
    print("=== Пример базового использования многоуровневого кэша ===")
    
    # Создаем многоуровневый кэш с двумя уровнями: Redis (приоритет 0) -> Memory (приоритет 1)
    cache = MultiLevelCache()
    await cache.initialize()
    
    # Устанавливаем значение
    await cache.set("example_key", "Hello, MultiLevel Cache!", ttl=300)
    
    # Получаем значение
    value = await cache.get("example_key")
    print(f"Полученное значение: {value}")
    
    # Проверяем, существует ли ключ
    exists = await cache.exists("example_key")
    print(f"Ключ существует: {exists}")
    
    # Удаляем значение
    await cache.delete("example_key")
    
    # Проверяем, что значение удалено
    value = await cache.get("example_key")
    print(f"Значение после удаления: {value}")
    
    await cache.close()


async def example_custom_levels():
    """Пример использования кастомных уровней кэша."""
    print("\n=== Пример использования кастомных уровней кэша ===")
    
    # Создаем кэши для разных уровней
    fast_cache = MemoryCache(max_size=100, default_ttl=60)
    slow_cache = MemoryCache(max_size=1000, default_ttl=300)
    
    # Определяем уровни: быстрый (приоритет 0) -> медленный (приоритет 1)
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=60),
        CacheLevel("slow", slow_cache, 1, default_ttl=300)
    ]
    
    # Создаем многоуровневый кэш с кастомными уровнями
    cache = MultiLevelCache(levels=levels, sync_strategy="write_through")
    
    # Инициализируем кэш (для MemoryCache запускается задача очистки)
    await cache.initialize()
    
    # Устанавливаем значение
    await cache.set("custom_key", "Custom Level Value", ttl=120)
    
    # Получаем значение
    value = await cache.get("custom_key")
    print(f"Значение из кастомного кэша: {value}")
    
    # Проверяем статус уровней
    level_status = cache.get_level_status()
    print(f"Статус уровней: {level_status}")
    
    await cache.close()


async def example_different_sync_strategies():
    """Пример использования разных стратегий синхронизации."""
    print("\n=== Пример использования разных стратегий синхронизации ===")
    
    # Создаем уровни кэша
    l1_cache = MemoryCache(max_size=50, default_ttl=60)
    l2_cache = MemoryCache(max_size=200, default_ttl=300)
    
    levels = [
        CacheLevel("L1", l1_cache, 0, default_ttl=60),
        CacheLevel("L2", l2_cache, 1, default_ttl=300)
    ]
    
    # Тестируем стратегию write-through
    print("\n--- Write-through стратегия ---")
    wt_cache = MultiLevelCache(levels=levels.copy(), sync_strategy="write_through")
    await wt_cache.initialize()
    
    await wt_cache.set("wt_key", "Write-through Value", ttl=120)
    
    # Значение должно быть в обоих уровнях
    l1_value = await l1_cache.get("wt_key")
    l2_value = await l2_cache.get("wt_key")
    print(f"L1 значение: {l1_value}")
    print(f"L2 значение: {l2_value}")
    
    await wt_cache.close()
    
    # Тестируем стратегию write-back
    print("\n--- Write-back стратегия ---")
    wb_cache = MultiLevelCache(levels=levels.copy(), sync_strategy="write_back")
    await wb_cache.initialize()
    
    await wb_cache.set("wb_key", "Write-back Value", ttl=120)
    
    # Значение должно быть только в L1 (самом быстром уровне)
    l1_value = await l1_cache.get("wb_key")
    l2_value = await l2_cache.get("wb_key")
    print(f"L1 значение: {l1_value}")
    print(f"L2 значение: {l2_value}")
    
    await wb_cache.close()


async def example_hash_operations():
    """Пример операций с хэшами."""
    print("\n=== Пример операций с хэшами ===")
    
    cache = MultiLevelCache()
    await cache.initialize()
    
    # Работа с хэшами
    await cache.hset("user_profile", "name", "John Doe", ttl=300)
    await cache.hset("user_profile", "email", "john@example.com", ttl=300)
    await cache.hset("user_profile", "age", 30, ttl=300)
    
    # Получаем отдельные поля
    name = await cache.hget("user_profile", "name")
    email = await cache.hget("user_profile", "email")
    age = await cache.hget("user_profile", "age")
    
    print(f"Имя: {name}, Email: {email}, Возраст: {age}")
    
    # Получаем все поля
    profile = await cache.hgetall("user_profile")
    print(f"Весь профиль: {profile}")
    
    # Удаляем поле
    deleted = await cache.hdel("user_profile", "email")
    print(f"Удалено полей: {deleted}")
    
    # Проверяем, что поле удалено
    email = await cache.hget("user_profile", "email")
    print(f"Email после удаления: {email}")
    
    await cache.close()


async def example_performance_comparison():
    """Пример сравнения производительности разных уровней."""
    print("\n=== Пример сравнения производительности ===")
    
    # Создаем кэш с разными уровнями
    fast_cache = MemoryCache(max_size=1000, default_ttl=60)
    slow_cache = MemoryCache(max_size=10000, default_ttl=600)
    
    levels = [
        CacheLevel("fast", fast_cache, 0, default_ttl=60),
        CacheLevel("slow", slow_cache, 1, default_ttl=600)
    ]
    
    cache = MultiLevelCache(levels=levels)
    await cache.initialize()
    
    # Устанавливаем много значений в медленный уровень
    for i in range(100):
        await slow_cache.set(f"slow_key_{i}", f"slow_value_{i}", ttl=600)
    
    # Измеряем время доступа к значениям
    start_time = time.time()
    for i in range(100):
        value = await cache.get(f"slow_key_{i}")
        # После первого доступа значение будет закэшировано в быстром уровне
    end_time = time.time()
    
    print(f"Время доступа к 100 значениям (включая кэширование): {end_time - start_time:.4f} секунд")
    
    # Теперь получаем значения снова - они должны быть в быстром кэше
    start_time = time.time()
    for i in range(100):
        value = await cache.get(f"slow_key_{i}")
    end_time = time.time()
    
    print(f"Время доступа к 100 значениям (из быстрого кэша): {end_time - start_time:.4f} секунд")
    
    await cache.close()


async def main():
    """Основная функция примера."""
    print("Демонстрация многоуровневого кэша")
    
    await example_basic_usage()
    await example_custom_levels()
    await example_different_sync_strategies()
    await example_hash_operations()
    await example_performance_comparison()
    
    print("\nВсе примеры выполнены успешно!")


if __name__ == "__main__":
    asyncio.run(main())