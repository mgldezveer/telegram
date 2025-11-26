"""
LLM Management Commands
Команды для управления LLM системой (только для администраторов)
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ...llm.config import get_config, reload_config
from ...llm.status_checker import StatusChecker
from ...llm.manager import LLMManager

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    import os
    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
    return str(user_id) in admin_ids


async def llm_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /llm_status - проверка статуса всех провайдеров
    
    Показывает:
    - Какие провайдеры включены
    - Доступность каждого провайдера
    - Время отклика
    - Ошибки если есть
    """
    # Проверка прав администратора
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам."
        )
        return
    
    await update.message.reply_text("🔍 Проверка статуса LLM провайдеров...")
    
    try:
        # Проверка статуса
        checker = StatusChecker()
        report = await checker.get_status_report()
        
        await update.message.reply_text(
            f"```\n{report}\n```",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in llm_status command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при проверке статуса: {e}"
        )


async def llm_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /llm_stats - статистика использования LLM
    
    Показывает:
    - Количество запросов к каждому провайдеру
    - Успешные/неудачные запросы
    - Использование кэша
    - Rate limit статус
    """
    # Проверка прав администратора
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам."
        )
        return
    
    try:
        # Получение менеджера
        manager = context.bot_data.get('llm_manager')
        
        if not manager:
            await update.message.reply_text(
                "⚠️ LLM Manager не инициализирован"
            )
            return
        
        # Получение статистики
        stats = manager.get_statistics()
        
        # Форматирование отчета
        report = "📊 LLM Statistics\n"
        report += "=" * 40 + "\n\n"
        
        # Общая статистика
        report += f"Total Requests: {stats['total_requests']}\n"
        report += f"Successful: {stats['successful_requests']}\n"
        report += f"Failed: {stats['failed_requests']}\n"
        
        if stats['total_requests'] > 0:
            success_rate = (stats['successful_requests'] / stats['total_requests']) * 100
            report += f"Success Rate: {success_rate:.1f}%\n"
        
        report += "\n"
        
        # Статистика по провайдерам
        report += "Provider Usage:\n"
        for provider, count in stats['provider_usage'].items():
            report += f"  • {provider}: {count} requests\n"
        
        report += "\n"
        
        # Кэш статистика
        cache_stats = stats.get('cache_stats', {})
        if cache_stats:
            report += "Cache Statistics:\n"
            report += f"  • Hits: {cache_stats.get('hits', 0)}\n"
            report += f"  • Misses: {cache_stats.get('misses', 0)}\n"
            
            total = cache_stats.get('hits', 0) + cache_stats.get('misses', 0)
            if total > 0:
                hit_rate = (cache_stats.get('hits', 0) / total) * 100
                report += f"  • Hit Rate: {hit_rate:.1f}%\n"
        
        await update.message.reply_text(
            f"```\n{report}\n```",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in llm_stats command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при получении статистики: {e}"
        )


async def llm_switch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /llm_switch <provider> - переключение на другой провайдер
    
    Аргументы:
        provider: groq, gemini, или huggingface
    """
    # Проверка прав администратора
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам."
        )
        return
    
    # Проверка аргументов
    if not context.args:
        await update.message.reply_text(
            "❌ Использование: /llm_switch <provider>\n"
            "Доступные провайдеры: groq, gemini, huggingface"
        )
        return
    
    provider_name = context.args[0].lower()
    
    try:
        # Получение менеджера
        manager = context.bot_data.get('llm_manager')
        
        if not manager:
            await update.message.reply_text(
                "⚠️ LLM Manager не инициализирован"
            )
            return
        
        # Проверка доступности провайдера
        config = get_config()
        provider_config = config.get_provider_config(provider_name)
        
        if not provider_config:
            await update.message.reply_text(
                f"❌ Провайдер '{provider_name}' не найден.\n"
                "Доступные: groq, gemini, huggingface"
            )
            return
        
        if not provider_config.enabled:
            await update.message.reply_text(
                f"❌ Провайдер '{provider_name}' отключен в конфигурации."
            )
            return
        
        # Переключение провайдера
        manager.set_preferred_provider(provider_name)
        
        await update.message.reply_text(
            f"✅ Переключено на провайдер: {provider_name}"
        )
        
    except Exception as e:
        logger.error(f"Error in llm_switch command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при переключении провайдера: {e}"
        )


async def llm_cache_clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /llm_cache_clear - очистка кэша LLM
    
    Удаляет все закэшированные ответы.
    """
    # Проверка прав администратора
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам."
        )
        return
    
    try:
        # Получение менеджера
        manager = context.bot_data.get('llm_manager')
        
        if not manager:
            await update.message.reply_text(
                "⚠️ LLM Manager не инициализирован"
            )
            return
        
        # Очистка кэша
        if hasattr(manager, 'cache') and manager.cache:
            await manager.cache.clear()
            await update.message.reply_text(
                "✅ Кэш LLM очищен"
            )
        else:
            await update.message.reply_text(
                "⚠️ Кэш не включен или недоступен"
            )
        
    except Exception as e:
        logger.error(f"Error in llm_cache_clear command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при очистке кэша: {e}"
        )


async def llm_reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /llm_reload - перезагрузка конфигурации LLM
    
    Перечитывает настройки из .env файла.
    """
    # Проверка прав администратора
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам."
        )
        return
    
    try:
        # Перезагрузка конфигурации
        config = reload_config()
        
        enabled_providers = config.get_enabled_providers()
        
        await update.message.reply_text(
            f"✅ Конфигурация LLM перезагружена\n\n"
            f"Включенные провайдеры: {', '.join(enabled_providers)}\n"
            f"Default: {config.default_provider}\n"
            f"Cache: {'✅' if config.cache_enabled else '❌'}\n"
            f"Fallback: {'✅' if config.fallback_enabled else '❌'}"
        )
        
    except Exception as e:
        logger.error(f"Error in llm_reload command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при перезагрузке конфигурации: {e}"
        )
