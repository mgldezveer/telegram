"""
Тестовый скрипт для проверки LLM системы.

Этот модуль содержит набор тестов для проверки функциональности
VibeCodingEngine, включая генерацию контента, кэширование и мониторинг.
"""

import asyncio
import logging
import time
from typing import Dict, Any

from src.services.vibe_coding_engine import VibeCodingEngine, VibeCodingRole

# Константы
SEPARATOR_LONG = "=" * 60
SEPARATOR_SHORT = "-" * 60
TEST_ITERATIONS = 3

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_test_header(test_number: int, description: str) -> None:
    """Печать заголовка теста."""
    print(f"\n{SEPARATOR_LONG}")
    print(f"🧪 ТЕСТ {test_number}: {description}")
    print(f"{SEPARATOR_LONG}\n")


def print_section(content: str, use_short_separator: bool = True) -> None:
    """Печать секции с разделителями."""
    separator = SEPARATOR_SHORT if use_short_separator else SEPARATOR_LONG
    print(separator)
    print(content)
    print(separator)


async def test_single_role() -> str:
    """
    Тест генерации для одной роли.
    
    Returns:
        str: Сгенерированный контент
    """
    print_test_header(1, "Генерация для одной роли (Главный мозг)")
    
    engine = VibeCodingEngine()
    
    topic = "Создать Telegram бота для управления задачами"
    
    print(f"📝 Тема: {topic}\n")
    print("⏳ Генерация контента...\n")
    
    try:
        content = await engine.generate_content_by_role(
            role=VibeCodingRole.MAIN_BRAIN,
            topic=topic
        )
        
        print("✅ Результат:")
        print_section(content)
        
        return content
    except Exception as e:
        logger.error(f"Ошибка при генерации контента: {e}")
        raise


async def test_all_roles() -> None:
    """Тест генерации для всех ролей."""
    print_test_header(2, "Генерация для всех 6 ролей")
    
    engine = VibeCodingEngine()
    
    topic = "Система аналитики для Telegram бота"
    
    print(f"📝 Тема: {topic}\n")
    
    role_names = {
        VibeCodingRole.MAIN_BRAIN: "🧠 Главный мозг",
        VibeCodingRole.PRD: "📋 PRD",
        VibeCodingRole.ARCHITECT: "🏗️ Архитектор",
        VibeCodingRole.CODE: "💻 Код",
        VibeCodingRole.DEBUG: "🐛 Дебаг",
        VibeCodingRole.CHILD: "👶 Детский"
    }
    
    for role in VibeCodingRole:
        print(f"\n⏳ Генерация: {role_names[role]}...")
        
        content = await engine.generate_content_by_role(
            role=role,
            topic=topic
        )
        
        print(f"✅ {role_names[role]} - {len(content)} символов")
    
    print("\n✅ Все роли сгенерированы успешно!")


def format_stats(stats: Dict[str, Any]) -> str:
    """
    Форматирование статистики для вывода.
    
    Args:
        stats: Словарь со статистикой
        
    Returns:
        str: Отформатированная строка
    """
    lines = []
    for key, value in stats.items():
        if isinstance(value, dict):
            lines.append(f"\n{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


async def test_stats() -> None:
    """Тест получения статистики."""
    print_test_header(3, "Статистика системы")
    
    engine = VibeCodingEngine()
    topic = "Простой пример"
    
    print(f"⏳ Делаем {TEST_ITERATIONS} запроса для сбора статистики...\n")
    
    try:
        for i in range(TEST_ITERATIONS):
            await engine.generate_content_by_role(
                role=VibeCodingRole.CHILD,
                topic=f"{topic} #{i+1}"
            )
            print(f"  ✓ Запрос {i+1}/{TEST_ITERATIONS} выполнен")
        
        stats = engine.get_stats()
        
        print("\n📊 Статистика:")
        if isinstance(stats, dict):
            print_section(format_stats(stats))
        else:
            print_section(str(stats))
            
    except Exception as e:
        logger.error(f"Ошибка при сборе статистики: {e}")
        raise


def format_health_status(health: Dict[str, Any]) -> str:
    """
    Форматирование статуса здоровья для вывода.
    
    Args:
        health: Словарь со статусом здоровья
        
    Returns:
        str: Отформатированная строка
    """
    lines = [
        f"Общий статус: {health.get('status', 'unknown')}",
        f"LLM доступен: {health.get('llm_available', False)}"
    ]
    
    if 'providers' in health:
        lines.append("\nПровайдеры:")
        for provider, status in health['providers'].items():
            emoji = "✅" if status else "❌"
            status_text = 'доступен' if status else 'недоступен'
            lines.append(f"  {emoji} {provider}: {status_text}")
    
    return "\n".join(lines)


async def test_health() -> None:
    """Тест проверки здоровья провайдеров."""
    print_test_header(4, "Проверка здоровья провайдеров")
    
    engine = VibeCodingEngine()
    
    print("⏳ Проверка доступности провайдеров...\n")
    
    try:
        health = await engine.get_health()
        
        print("🏥 Статус здоровья:")
        print_section(format_health_status(health))
        
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья: {e}")
        raise


async def test_cache():
    """Тест кэширования"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 5: Проверка кэширования")
    print("="*60 + "\n")
    
    engine = VibeCodingEngine()
    
    topic = "Тест кэширования"
    role = VibeCodingRole.CHILD
    
    print("⏳ Первый запрос (без кэша)...")
    import time
    start = time.time()
    content1 = await engine.generate_content_by_role(role, topic)
    time1 = time.time() - start
    print(f"✅ Выполнено за {time1:.2f}s")
    
    print("\n⏳ Второй запрос (с кэшем)...")
    start = time.time()
    content2 = await engine.generate_content_by_role(role, topic)
    time2 = time.time() - start
    print(f"✅ Выполнено за {time2:.2f}s")
    
    print(f"\n📊 Результаты:")
    print(f"  Первый запрос: {time1:.2f}s")
    print(f"  Второй запрос: {time2:.2f}s")
    
    if time2 < time1:
        speedup = time1 / time2
        print(f"  🚀 Ускорение: {speedup:.1f}x")
    
    # Проверяем статистику кэша
    stats = engine.get_stats()
    if 'cache' in stats:
        cache_stats = stats['cache']
        print(f"\n💾 Статистика кэша:")
        print(f"  Hit rate: {cache_stats.get('hit_rate', 0)}%")
        print(f"  Hits: {cache_stats.get('hits', 0)}")
        print(f"  Misses: {cache_stats.get('misses', 0)}")


async def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("🚀 ТЕСТИРОВАНИЕ LLM СИСТЕМЫ")
    print("="*60)
    
    try:
        # Тест 1: Одна роль
        await test_single_role()
        
        # Тест 2: Все роли
        await test_all_roles()
        
        # Тест 3: Статистика
        await test_stats()
        
        # Тест 4: Здоровье
        await test_health()
        
        # Тест 5: Кэширование
        await test_cache()
        
        print("\n" + "="*60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
