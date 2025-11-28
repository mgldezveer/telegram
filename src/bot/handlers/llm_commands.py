<![CDATA[
"""
LLM Management Commands - Admin commands for LLM system control
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from src.config import config
from src.llm import get_config
from src.llm.metrics import get_metrics
from src.llm.rate_limit_manager import RateLimitManager
from src.llm.models import get_available_models

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in config.bot.admin_ids


def validate_provider_name(provider: str) -> bool:
    """Validate provider name."""
    valid_providers = ['groq', 'gemini', 'huggingface', 'openai', 'anthropic']
    return provider.lower() in valid_providers


def validate_prompt_length(prompt: str) -> tuple[bool, str]:
    """Validate prompt length."""
    if len(prompt) < 1:
        return False, "Prompt cannot be empty"
    if len(prompt) > 4000:  # Increased max length
        return False, "Prompt is too long (maximum 4000 characters)"
    return True, ""


def sanitize_prompt(prompt: str) -> str:
    """Sanitize prompt to prevent injection attacks."""
    # Remove potentially dangerous patterns
    dangerous_patterns = ['<script', 'javascript:', 'onerror', 'onload', 'eval(', 'exec(', 'system:', 'prompt:', 'ignore', 'forget', 'instruction', 'output:']
    sanitized = prompt.lower()
    for pattern in dangerous_patterns:
        if pattern in sanitized:
            # Remove the dangerous pattern
            sanitized = sanitized.replace(pattern, '')
    return prompt  # Return original prompt with dangerous parts removed


def validate_temperature(temp_str: str) -> tuple[bool, float]:
    """Validate temperature value."""
    try:
        temp = float(temp_str)
        if 0.0 <= temp <= 2.0:
            return True, temp
        return False, 0.0
    except ValueError:
        return False, 0.0


def validate_max_tokens(token_str: str) -> tuple[bool, int]:
    """Validate max_tokens value."""
    try:
        tokens = int(token_str)
        if 1 <= tokens <= 4096:
            return True, tokens
        return False, 0
    except ValueError:
        return False, 0


async def llm_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show LLM system status.
    
    Usage: /llm_status
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        # Get configuration
        config = get_config()
        
        # Get status summary
        status_text = config.get_status_summary()
        
        # Check provider availability
        if hasattr(context.bot_data, 'llm_manager') and context.bot_data.llm_manager:
            llm_manager = context.bot_data.llm_manager
            
            status_text += "\n\n🔍 Доступность провайдеров:"
            availability = await llm_manager.check_providers_availability()
            
            for provider, is_available in availability.items():
                status = "✅ Доступен" if is_available else "❌ Недоступен"
                status_text += f"\n  {provider.capitalize()}: {status}"
        else:
            status_text += "\n\n⚠️ LLM Manager недоступен"
        
        await update.message.reply_text(status_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in llm_status command: {e}")
        await update.message.reply_text(f"❌ Ошибка получения статуса LLM: {str(e)[:200]}...")


async def llm_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show LLM usage statistics.
    
    Usage: /llm_stats
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        # Get metrics
        metrics = get_metrics()
        stats = metrics.get_statistics()
        
        # Format statistics
        text = "📊 <b>Статистика использования LLM</b>\n\n"
        text += "=" * 40 + "\n\n"
        
        # Provider stats
        if stats['providers']:
            text += "<b>Провайдеры:</b>\n"
            for provider, provider_stats in stats['providers'].items():
                text += f"\n<b>{provider.capitalize()}:</b>\n"
                text += f"  Всего запросов: {provider_stats['total_requests']}\n"
                text += f"  Успешных: {provider_stats['successes']}\n"
                text += f"  Ошибок: {provider_stats['failures']}\n"
                text += f" Успехов: {provider_stats['success_rate']}%\n"
                text += f"  Средняя задержка: {provider_stats['avg_latency_seconds']:.2f}s\n"
                text += f"  Лимиты: {provider_stats['rate_limit_hits']}\n"
        else:
            text += "Статистика провайдеров недоступна\n"
        
        text += "\n"
        
        # Cache stats
        if 'cache' in stats:
            text += "<b>Кэш:</b>\n"
            text += f"  Процент попаданий: {stats['cache']['hit_rate']}%\n"
            text += f"  Попаданий: {stats['cache']['hits']}\n"
            text += f" Промахов: {stats['cache']['misses']}\n"
        else:
            text += "<b>Кэш: отключен</b>\n"
        
        text += f"\nПоследнее обновление: {stats['timestamp']}"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in llm_stats command: {e}")
        await update.message.reply_text(f"❌ Ошибка получения статистики LLM: {str(e)[:200]}...")


async def llm_switch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Switch preferred LLM provider.
    
    Usage: /llm_switch <provider>
    Example: /llm_switch groq
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args:
        keyboard = [
            [InlineKeyboardButton("🔄 Groq", callback_data="llm_switch_groq")],
            [InlineKeyboardButton("🔄 Gemini", callback_data="llm_switch_gemini")],
            [InlineKeyboardButton("🔄 HuggingFace", callback_data="llm_switch_huggingface")],
            [InlineKeyboardButton("🔄 OpenAI", callback_data="llm_switch_openai")],
            [InlineKeyboardButton("🔄 Anthropic", callback_data="llm_switch_anthropic")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔄 Выберите провайдер для переключения:",
            reply_markup=reply_markup
        )
        return
    
    provider = context.args[0].lower()
    if not validate_provider_name(provider):
        await update.message.reply_text(
            f"❌ Неверный провайдер: {provider}\n\n"
            f"Доступные провайдеры: groq, gemini, huggingface, openai, anthropic"
        )
        return
    
    try:
        # Store preferred provider in bot data
        context.bot_data['preferred_llm_provider'] = provider
        
        await update.message.reply_text(
            f"✅ Основной провайдер LLM изменен на: {provider.capitalize()}\n\n"
            f"Примечание: Резервные провайдеры будут использоваться при отказе основного."
        )
        
        logger.info(f"Admin {update.effective_user.id} switched LLM provider to {provider}")
        
    except Exception as e:
        logger.error(f"Error in llm_switch command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка переключения провайдера: {str(e)[:200]}...")


async def llm_models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show available LLM models for each provider.
    
    Usage: /llm_models [provider]
    Example: /llm_models groq
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        provider = context.args[0].lower() if context.args else None
        if provider and not validate_provider_name(provider):
            await update.message.reply_text(
                f"❌ Неверный провайдер: {provider}\n\n"
                f"Доступные провайдеры: groq, gemini, huggingface, openai, anthropic"
            )
            return
        
        available_models = get_available_models()
        text = "🤖 <b>Доступные модели LLM</b>\n\n"
        
        if provider:
            if provider in available_models:
                text += f"<b>{provider.capitalize()}:</b>\n"
                for model in available_models[provider]:
                    text += f"  • {model}\n"
            else:
                text += f"❌ Провайдер {provider} не поддерживается или не настроен"
        else:
            for prov, models in available_models.items():
                text += f"<b>{prov.capitalize()}:</b>\n"
                for model in models:
                    text += f"  • {model}\n"
                text += "\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in llm_models command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка получения моделей: {str(e)[:200]}...")


async def llm_set_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Set the default model for a provider.
    
    Usage: /llm_set_model <provider> <model_name>
    Example: /llm_set_model groq llama3-70b-8192
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /llm_set_model <provider> <model_name>\n"
            "Пример: /llm_set_model groq llama3-70b-8192"
        )
        return
    
    provider = context.args[0].lower()
    model_name = context.args[1]
    
    if not validate_provider_name(provider):
        await update.message.reply_text(
            f"❌ Неверный провайдер: {provider}\n\n"
            f"Доступные провайдеры: groq, gemini, huggingface, openai, anthropic"
        )
        return
    
    try:
        available_models = get_available_models()
        if provider not in available_models or model_name not in available_models[provider]:
            await update.message.reply_text(
                f"❌ Модель {model_name} не доступна для провайдера {provider}\n\n"
                f"Доступные модели: {', '.join(available_models.get(provider, []))}"
            )
            return
        
        # Update the configuration
        config = get_config()
        config.set_default_model(provider, model_name)
        
        await update.message.reply_text(
            f"✅ Модель по умолчанию для {provider} установлена на: {model_name}"
        )
        
        logger.info(f"Admin {update.effective_user.id} set default model for {provider} to {model_name}")
        
    except Exception as e:
        logger.error(f"Error in llm_set_model command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка установки модели: {str(e)[:200]}...")


async def llm_cache_clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clear LLM response cache.
    
    Usage: /llm_cache_clear
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        # Get LLM manager to check if cache exists
        if hasattr(context.bot_data, 'llm_manager') and context.bot_data.llm_manager:
            llm_manager = context.bot_data.llm_manager
            if not hasattr(llm_manager, 'cache_service') or not llm_manager.cache_service:
                await update.message.reply_text("⚠️ Кэш LLM не включен")
                return
        else:
            await update.message.reply_text("❌ Менеджер LLM недоступен")
            return
        
        # Confirm action
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_cache_clear")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ Вы уверены, что хотите очистить кэш LLM?\n\n"
            "Все закэшированные ответы будут удалены.",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in llm_cache_clear command: {e}")
        await update.message.reply_text(f"❌ Ошибка очистки кэша: {str(e)[:200]}...")


async def llm_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Test LLM generation.
    
    Usage: /llm_test <prompt> [temperature] [max_tokens]
    Example: /llm_test Write a short greeting 0.7 150
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /llm_test <prompt> [temperature] [max_tokens]\n"
            "Пример: /llm_test Напиши приветствие 0.7 150\n"
            "Температура: 0.0-2.0 (по умолчанию 0.7)\n"
            "Макс. токенов: 1-4096 (по умолчанию 500)"
        )
        return
    
    prompt = " ".join(context.args[:len(context.args)-2]) if len(context.args) > 2 else " ".join(context.args)
    temperature = 0.7
    max_tokens = 500
    
    # Parse optional parameters if provided
    if len(context.args) > 1:
        temp_arg = context.args[-2] if len(context.args) > 2 else None
        token_arg = context.args[-1] if len(context.args) > 1 else None
        
        if temp_arg and token_arg:
            is_valid_temp, temp_val = validate_temperature(temp_arg)
            if is_valid_temp:
                temperature = temp_val
                is_valid_token, token_val = validate_max_tokens(token_arg)
                if is_valid_token:
                    max_tokens = token_val
                else:
                    is_valid_token, token_val = validate_max_tokens(temp_arg)
                    if is_valid_token:
                        max_tokens = token_val
            else:
                is_valid_token, token_val = validate_max_tokens(temp_arg)
                if is_valid_token:
                    max_tokens = token_val
                else:
                    # Both args might be in wrong order, try parsing the last one as tokens
                    is_valid_token, token_val = validate_max_tokens(token_arg)
                    if is_valid_token:
                        max_tokens = token_val
        elif len(context.args) > 1:
            # Try to parse the last argument as either temperature or max_tokens
            last_arg = context.args[-1]
            is_valid_temp, temp_val = validate_temperature(last_arg)
            if is_valid_temp:
                temperature = temp_val
            else:
                is_valid_token, token_val = validate_max_tokens(last_arg)
                if is_valid_token:
                    max_tokens = token_val
    
    # Sanitize the prompt
    prompt = sanitize_prompt(prompt)
    
    is_valid, error_msg = validate_prompt_length(prompt)
    if not is_valid:
        await update.message.reply_text(f"❌ {error_msg}")
        return
    
    # Additional validation for potentially harmful content
    if any(keyword in prompt.lower() for keyword in ['system:', 'prompt:', 'ignore', 'forget', 'instruction', 'output:']):
        await update.message.reply_text("❌ Потенциально опасный запрос отклонен")
        logger.warning(f"Blocked potentially harmful prompt from user {update.effective_user.id}: {prompt[:100]}...")
        return
    
    try:
        # Get LLM manager
        if hasattr(context.bot_data, 'llm_manager') and context.bot_data.llm_manager:
            llm_manager = context.bot_data.llm_manager
            
            await update.message.reply_text(f"⏳ Генерирую ответ...\nТемп: {temperature}, Токены: {max_tokens}")
            
            # Generate with error handling
            try:
                response = await llm_manager.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                response_length = len(response)
                if response_length > 1000:
                    # Send as document if too long
                    from io import StringIO
                    import io
                    bio = io.BytesIO(response.encode('utf-8'))
                    bio.name = 'llm_response.txt'
                    await update.message.reply_document(
                        document=bio,
                        caption=f"✅ Ответ LLM ({response_length} символов)"
                    )
                else:
                    # Sanitize response before sending
                    safe_response = response.replace('<', '<').replace('>', '>')
                    await update.message.reply_text(
                        f"✅ Ответ LLM:\n\n{safe_response}\n\n"
                        f"Длина: {response_length} символов\n"
                        f"Темп: {temperature}, Токены: {max_tokens}"
                    )
                
                logger.info(f"Admin {update.effective_user.id} tested LLM with prompt: {prompt[:50]}...")
            except Exception as gen_error:
                logger.error(f"LLM generation error: {gen_error}", exc_info=True)
                await update.message.reply_text(f"❌ Ошибка генерации: {str(gen_error)[:200]}...")
        else:
            await update.message.reply_text("❌ Менеджер LLM недоступен")
        
    except Exception as e:
        logger.error(f"Error in llm_test command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка тестирования LLM: {str(e)[:200]}...")


async def llm_monitoring_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show detailed LLM monitoring information.
    
    Usage: /llm_monitoring
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        from src.llm.status_checker import check_providers_status
        statuses = await check_providers_status()
        
        text = "🔍 <b>Мониторинг провайдеров LLM</b>\n\n"
        text += "=" * 40 + "\n\n"
        
        for name, status in statuses.items():
            status_emoji = "✅" if status.available else "❌" if status.enabled else "⚠️"
            text += f"<b>{status_emoji} {name.capitalize()}:</b>\n"
            text += f"  Включено: {'Да' if status.enabled else 'Нет'}\n"
            text += f"  Доступно: {'Да' if status.available else 'Нет'}\n"
            if status.response_time > 0:
                text += f"  Время отклика: {status.response_time:.2f}s\n"
            if status.error:
                text += f"  Ошибка: {status.error}\n"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in llm_monitoring command: {e}")
        await update.message.reply_text(f"❌ Ошибка мониторинга LLM: {str(e)[:200]}...")


async def llm_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show LLM configuration details.
    
    Usage: /llm_config
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        config = get_config()
        status_text = config.get_status_summary()
        await update.message.reply_text(f"<pre>{status_text}</pre>", parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in llm_config command: {e}")
        await update.message.reply_text(f"❌ Ошибка получения конфигурации: {e}")


async def llm_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show LLM commands help.
    
    Usage: /llm_help
    """
    help_text = """
 📚 <b>Команды управления LLM:</b>

 <b>Мониторинг:</b>
 • /llm_status - Статус системы
 • /llm_stats - Статистика использования
 • /llm_monitoring - Подробный мониторинг
 • /llm_config - Конфигурация

 <b>Управление:</b>
 • /llm_switch - Сменить провайдер
 • /llm_models - Доступные модели
 • /llm_set_model - Установить модель
 • /llm_cache_clear - Очистить кэш
 • /llm_test - Тест генерации

 <b>Справка:</b>
 • /llm_help - Эта справка
     """
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def llm_rate_limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show and manage rate limits for users.
    
    Usage: /llm_rate_limit [user_id] [limit]
    Example: /llm_rate_limit 123456789 10
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        rate_limit_manager = RateLimitManager()
        if not context.args:
            # Show current rate limits
            limits = rate_limit_manager.get_all_limits()
            text = "📊 <b>Текущие лимиты запросов к LLM</b>\n\n"
            if limits:
                for user_id, limit in limits.items():
                    text += f"User {user_id}: {limit} запросов\n"
            else:
                text = "Лимиты не установлены. Все пользователи используют стандартные лимиты."
            await update.message.reply_text(text, parse_mode='HTML')
            return
        
        if len(context.args) == 1:
            # Show rate limit for specific user
            user_id = int(context.args[0])
            limit = rate_limit_manager.get_user_limit(user_id)
            current_count = rate_limit_manager.get_user_count(user_id)
            reset_time = rate_limit_manager.get_reset_time(user_id)
            await update.message.reply_text(
                f"📊 Лимиты для пользователя {user_id}:\n"
                f"Установленный лимит: {limit} запросов\n"
                f"Использовано: {current_count} запросов\n"
                f"Сброс через: {reset_time} секунд"
            )
            return
        
        if len(context.args) == 2:
            # Set rate limit for user
            user_id = int(context.args[0])
            new_limit = int(context.args[1])
            if new_limit < 0:
                await update.message.reply_text("❌ Лимит не может быть отрицательным")
                return
            rate_limit_manager.set_user_limit(user_id, new_limit)
            await update.message.reply_text(
                f"✅ Лимит запросов для пользователя {user_id} установлен на {new_limit}"
            )
            logger.info(f"Admin {update.effective_user.id} set rate limit for {user_id} to {new_limit}")
            return
            
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID пользователя или лимита")
    except Exception as e:
        logger.error(f"Error in llm_rate_limit command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка управления лимитами: {str(e)[:200]}...")


# Export command handlers
__all__ = [
    'llm_status_command',
    'llm_stats_command',
    'llm_switch_command',
    'llm_cache_clear_command',
    'llm_test_command',
    'llm_monitoring_command',
    'llm_config_command',
    'llm_help_command',
]
]]>