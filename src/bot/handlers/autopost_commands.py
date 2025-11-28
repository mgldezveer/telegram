<![CDATA[
"""Auto-posting bot commands with new functionality."""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from src.config import config
from src.services.autopost import (
    AutoPostChannelManager,
    ChannelConfig,
    AutoPostContentGenerator,
    ContentStyle,
    AutoPostScheduler,
    ScheduleConfig,
    AutoPostQueueManager
)
from src.models.autopost import ScheduleMode, PostStatus
from src.services.content_source_manager import ContentSourceManager
from src.monitoring.realtime_error_detector import realtime_error_detector
from src.services.telegram_analytics_connector import TelegramAnalyticsConnector

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in config.bot.admin_ids


def validate_channel_id(channel_id_str: str) -> bool:
    """Validate channel ID format."""
    try:
        # Remove any spaces and validate format
        channel_id_str = channel_id_str.strip()
        if not channel_id_str:
            return False
            
        # Check if it's a valid channel ID format
        if channel_id_str.startswith('@'):
            # Username format
            return len(channel_id_str) > 1 and re.match(r'^@[a-zA-Z][a-zA-Z0-9_]{2,31}$', channel_id_str)
        else:
            # Numeric ID format
            channel_id = int(channel_id_str)
            return str(channel_id).startswith('-100') or str(channel_id).startswith('-') or channel_id < 0
    except ValueError:
        return False


def validate_time_slots(time_slots_str: str) -> tuple[bool, list[str]]:
    """Validate time slots format."""
    try:
        time_slots = time_slots_str.split(',')
        validated_slots = []
        
        for slot in time_slots:
            slot = slot.strip()
            if not slot:
                continue  # Skip empty slots
            parts = slot.split(':')
            if len(parts) != 2:
                return False, []
            
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False, []
            
            validated_slots.append(f"{hour:02d}:{minute:02d}")
        
        return True, validated_slots
    except ValueError:
        return False, []


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '&', '"', "'"]
    sanitized = text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized


def validate_theme(theme: str) -> tuple[bool, str]:
    """Validate theme input."""
    if not theme or len(theme.strip()) < 3:
        return False, "Тема слишком короткая (минимум 3 символа)"
    if len(theme) > 200:
        return False, "Тема слишком длинная (максимум 200 символов)"
    if not re.match(r'^[\w\s\-\.,!?а-яА-ЯёЁ]+$', theme):
        return False, "Тема содержит недопустимые символы"
    return True, ""


def validate_frequency(frequency: str) -> tuple[bool, int]:
    """Validate posting frequency."""
    try:
        freq = int(frequency)
        if freq < 1 or freq > 24:
            return False, 0
        return True, freq
    except ValueError:
        return False, 0


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        return f"{seconds // 60} мин"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} ч {minutes} мин"
        return f"{hours} ч"


async def autopost_add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add channel for auto-posting.
    
    Usage: /autopost_add_channel <channel_id> <name> [frequency]
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_add_channel <channel_id> <name> [frequency]\n"
            "Пример: /autopost_add_channel -1001234567890 'Мой канал' 3\n"
            "Частота указывается в постах в день (по умолчанию 3)"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -100 (публичный) или - (приватный), или быть @username"
            )
            return
        
        channel_id = int(channel_id_str) if not channel_id_str.startswith('@') else channel_id_str
        channel_name = context.args[1]
        
        # Sanitize channel name
        channel_name = sanitize_input(channel_name)
        
        if len(channel_name) > 100:
            await update.message.reply_text("❌ Название канала слишком длинное (максимум 100 символов)")
            return
        
        if len(channel_name) < 1:
            await update.message.reply_text("❌ Название канала не может быть пустым")
            return
        
        # Parse frequency if provided
        frequency = 3  # default
        if len(context.args) > 2:
            is_valid_freq, freq_val = validate_frequency(context.args[2])
            if not is_valid_freq:
                await update.message.reply_text("❌ Неверная частота публикаций (1-24 постов в день)")
                return
            frequency = freq_val
        
        # Get channel manager from bot_data
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        
        # Check if channel already exists
        existing_channel = await channel_manager.get_channel(channel_id)
        if existing_channel:
            if existing_channel.is_active:
                await update.message.reply_text(
                    f"❌ Канал {channel_id} уже существует в системе автопостинга"
                )
                return
            else:
                # Channel exists but is inactive, ask for confirmation to reactivate
                keyboard = [
                    [InlineKeyboardButton("✅ Активировать", callback_data=f"reactivate_channel_{channel_id}")],
                    [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"⚠️ Канал {channel_id} уже существует, но деактивирован.\n"
                    f"Активировать его заново?",
                    reply_markup=reply_markup
                )
                return
        
        # Check permissions first
        permissions = await channel_manager.check_permissions(channel_id)
        if not permissions.has_access:
            await update.message.reply_text(
                f"❌ Нет доступа каналу {channel_id}\n"
                f"Ошибка: {permissions.error}"
            )
            return
        
        if not permissions.can_post:
            await update.message.reply_text(
                f"❌ Бот не может публиковать посты в канал {channel_id}\n"
                f"Убедитесь, что бот добавлен в администраторы канала"
            )
            return
        
        # Add channel with settings
        config_obj = ChannelConfig(name=channel_name)
        channel = await channel_manager.add_channel(
            channel_id,
            config_obj,
            settings={'post_frequency': frequency}
        )
        
        await update.message.reply_text(
            f"✅ Канал добавлен для автопостинга!\n\n"
            f"ID: <code>{channel.id}</code>\n"
            f"Название: {channel.name}\n"
            f"Частота: {frequency} постов/день\n"
            f"Статус: {'Активен' if channel.is_active else 'Неактивен'}\n"
            f"Доступ: {'Да' if permissions.can_post else 'Нет'}",
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка формата данных: {e}")
        realtime_error_detector.track_exception(
            e,
            "autopost_commands",
            user_id=str(update.effective_user.id),
            chat_id=str(update.effective_chat.id),
            command="/autopost_add_channel",
            extra_data={"channel_id": context.args[0] if context.args else None}
        )
    except Exception as e:
        logger.error(f"Failed to add channel: {e}", exc_info=True)
        realtime_error_detector.track_exception(
            e,
            "autopost_commands",
            user_id=str(update.effective_user.id),
            chat_id=str(update.effective_chat.id),
            command="/autopost_add_channel",
            extra_data={"channel_id": context.args[0] if context.args else None}
        )
        await update.message.reply_text(f"❌ Ошибка при добавлении канала: {str(e)[:200]}...")


async def autopost_remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove channel from auto-posting.
    
    Usage: /autopost_remove_channel <channel_id>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_remove_channel <channel_id>\n"
            "Пример: /autopost_remove_channel -1001234567890"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -100 (публичный) или - (приватный)"
            )
            return
        
        channel_id = int(channel_id_str)
        
        # Validate that channel_id is a valid integer within reasonable range
        if abs(channel_id) < 1000:
            await update.message.reply_text("❌ Неверный ID канала")
            return
        
        # Get channel manager
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        
        # Check if channel exists
        channel = await channel_manager.get_channel(channel_id)
        if not channel:
            await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе")
            return
        
        # Confirm removal
        keyboard = [
            [InlineKeyboardButton("✅ Удалить", callback_data=f"remove_channel_{channel_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"⚠️ Вы уверены, что хотите удалить канал из автопостинга?\n\n"
            f"ID: <code>{channel.id}</code>\n"
            f"Название: {channel.name}\n\n"
            f"Все посты для этого канала будут отменены!",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка формата данных: {e}")
        realtime_error_detector.track_exception(
            e,
            "autopost_commands",
            user_id=str(update.effective_user.id),
            chat_id=str(update.effective_chat.id),
            command="/autopost_remove_channel",
            extra_data={"channel_id": context.args[0] if context.args else None}
        )
    except Exception as e:
        logger.error(f"Failed to remove channel: {e}")
        realtime_error_detector.track_exception(
            e,
            "autopost_commands",
            user_id=str(update.effective_user.id),
            chat_id=str(update.effective_chat.id),
            command="/autopost_remove_channel",
            extra_data={"channel_id": context.args[0] if context.args else None}
        )
        await update.message.reply_text(f"❌ Ошибка при удалении канала: {str(e)[:200]}...")


async def autopost_list_channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List auto-posting channels.
    
    Usage: /autopost_list_channels
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        
        channels = await channel_manager.list_channels(active_only=True)
        
        if not channels:
            await update.message.reply_text("📋 Нет активных каналов для автопостинга")
            return
        
        text = "📋 <b>Каналы для автопостинга:</b>\n\n"
        
        for i, channel in enumerate(channels, 1):
            settings = channel.settings or {}
            text += f"<b>{i}. {channel.name}</b>\n"
            text += f"ID: <code>{channel.id}</code>\n"
            text += f"Частота: {settings.get('post_frequency', 3)} постов/день\n"
            text += f"Автопубликация: {'Да' if settings.get('auto_publish', True) else 'Нет'}\n"
            text += f"Модерация: {'Да' if settings.get('require_moderation', False) else 'Нет'}\n"
            text += f"Постов сегодня: {settings.get('posts_today', 0)}\n"
            
            # Get channel info from Telegram if possible
            channel_info = await channel_manager.get_channel_info(channel.id)
            if channel_info and not channel_info.get('from_db', False):
                text += f"Имя: {channel_info.get('title', 'Не указано')}\n"
                if channel_info.get('username'):
                    text += f"Имя пользователя: @{channel_info['username']}\n"
            
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to list channels: {e}", exc_info=True)
        realtime_error_detector.track_exception(
            e,
            "autopost_commands",
            user_id=str(update.effective_user.id),
            chat_id=str(update.effective_chat.id),
            command="/autopost_list_channels"
        )
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def autopost_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics for auto-posting.
    
    Usage: /autopost_stats [channel_id]
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        channel_id = None
        if context.args:
            channel_id_str = context.args[0]
            if not validate_channel_id(channel_id_str):
                await update.message.reply_text(
                    "❌ Неверный формат ID канала!\n"
                    "ID канала должен начинаться с -100 (публичный) или - (приватный)"
                )
                return
            channel_id = int(channel_id_str)
        
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        
        # Get channel statistics
        if channel_id:
            channel = await channel_manager.get_channel(channel_id)
            if not channel:
                await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе")
                return
            
            stats = await channel_manager.get_channel_stats(channel_id)
            text = f"📊 <b>Статистика для канала {channel.name}</b>\n\n"
            text += f"ID: <code>{channel.id}</code>\n"
            text += f"Постов за сегодня: {stats.get('posts_today', 0)}\n"
            text += f"Постов за неделю: {stats.get('posts_this_week', 0)}\n"
            text += f"Постов за месяц: {stats.get('posts_this_month', 0)}\n"
            text += f"Успешных публикаций: {stats.get('successful_posts', 0)}\n"
            text += f"Ошибок публикации: {stats.get('failed_posts', 0)}\n"
        else:
            all_channels = await channel_manager.list_channels(active_only=True)
            total_posts_today = sum(
                (await channel_manager.get_channel_stats(ch.id)).get('posts_today', 0)
                for ch in all_channels
            )
            total_posts_week = sum(
                (await channel_manager.get_channel_stats(ch.id)).get('posts_this_week', 0)
                for ch in all_channels
            )
            total_channels = len(all_channels)
            
            text = "📊 <b>Общая статистика автопостинга</b>\n\n"
            text += f"Каналов: {total_channels}\n"
            text += f"Постов за сегодня: {total_posts_today}\n"
            text += f"Постов за неделю: {total_posts_week}\n"
            text += f"Всего постов: {sum(ch.settings.get('total_posts', 0) for ch in all_channels if ch.settings)}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        realtime_error_detector.track_exception(
            e,
            "autopost_commands",
            user_id=str(update.effective_user.id),
            chat_id=str(update.effective_chat.id),
            command="/autopost_stats",
            extra_data={"channel_id": context.args[0] if context.args else None}
        )
        await update.message.reply_text(f"❌ Ошибка получения статистики: {e}")


async def autopost_generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate post for auto-posting.
    
    Usage: /autopost_generate <channel_id> <theme>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_generate <channel_id> <theme>\n"
            "Пример: /autopost_generate -1001234567890 технологии"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -100 (публичный) или - (приватный)"
            )
            return
        
        channel_id = int(channel_id_str)
        theme = " ".join(context.args[1:])
        
        # Validate theme
        is_valid_theme, theme_error = validate_theme(theme)
        if not is_valid_theme:
            await update.message.reply_text(f"❌ {theme_error}")
            return
        
        # Sanitize theme
        theme = sanitize_input(theme)
        
        # Validate channel_id range
        if abs(channel_id) < 10000:
            await update.message.reply_text("❌ Неверный ID канала")
            return
        
        # Get channel manager to check if channel exists
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        channel = await channel_manager.get_channel(channel_id)
        if not channel:
            await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе автопостинга")
            return
        
        await update.message.reply_text(f"⏳ Генерирую пост на тему '{theme}'...")
        
        # Get LLM manager
        llm_manager = context.bot_data.get('llm_manager')
        
        # Generate post
        generator = AutoPostContentGenerator(llm_manager)
        style = ContentStyle(tone="professional", length="medium", format="news")
        post = await generator.generate_post(theme, style, channel_id)
        
        # Add to queue
        queue_manager = AutoPostQueueManager()
        queue_id = await queue_manager.add_to_queue(post)
        
        # Format preview
        preview = f"📝 <b>Пост сгенерирован и добавлен в очередь</b>\n\n"
        preview += f"ID: <code>{queue_id[:8]}</code>\n"
        preview += f"Канал: <code>{channel_id}</code>\n"
        preview += f"Тема: {theme}\n"
        preview += f"Статус: {post.status}\n\n"
        preview += f"<b>Контент:</b>\n{post.content[:500]}"
        
        if len(post.content) > 500:
            preview += "..."
        
        # Add moderation buttons if required
        settings = channel.settings or {}
        if settings.get('require_moderation', False):
            keyboard = [
                [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_post_{queue_id}")],
                [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_post_{queue_id}")],
                [InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_post_{queue_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            preview += "\n\nВыберите действие:"
            await update.message.reply_text(preview, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await update.message.reply_text(preview, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to generate post: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка генерации: {str(e)[:200]}...")


async def autopost_approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve post for publication.
    
    Usage: /autopost_approve <post_id>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_approve <post_id>\n"
            "Пример: /autopost_approve abc123def456"
        )
        return
    
    try:
        post_id = context.args[0]
        
        # Validate post_id format (should be a valid UUID-like string)
        if len(post_id) < 8 or len(post_id) > 64 or not post_id.replace('-', '').replace(' ', '').isalnum():
            await update.message.reply_text(f"❌ Неверный формат ID поста: {post_id}")
            return
        
        queue_manager = AutoPostQueueManager()
        queued_post = await queue_manager.get_post(post_id)
        if not queued_post:
            await update.message.reply_text(f"❌ Пост с ID {post_id} не найден")
            return
        
        if queued_post.status == PostStatus.APPROVED.value:
            await update.message.reply_text(f"✅ Пост {post_id} уже одобрен")
            return
        
        success = await queue_manager.approve_post(post_id)
        if success:
            await update.message.reply_text(f"✅ Пост {post_id} одобрен для публикации")
        else:
            await update.message.reply_text(f"❌ Ошибка одобрения поста {post_id}")
        
    except Exception as e:
        logger.error(f"Failed to approve post: {e}")
        await update.message.reply_text(f"❌ Ошибка одобрения: {str(e)[:200]}...")


async def autopost_queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View post queue.
    
    Usage: /autopost_queue [channel_id]
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        channel_id = None
        if context.args:
            channel_id_str = context.args[0]
            if not validate_channel_id(channel_id_str):
                await update.message.reply_text(
                    "❌ Неверный формат ID канала!\n"
                    "ID канала должен начинаться с -100 (публичный) или - (приватный)"
                )
                return
            channel_id = int(channel_id_str)
            
            # Validate channel_id range
            if abs(channel_id) < 10000:
                await update.message.reply_text("❌ Неверный ID канала")
                return
        
        queue_manager = AutoPostQueueManager()
        queue = await queue_manager.get_queue(channel_id=channel_id)
        
        if not queue:
            if channel_id:
                await update.message.reply_text(f"📋 Очередь постов для канала {channel_id} пуста")
            else:
                await update.message.reply_text("📋 Очередь постов пуста")
            return
        
        text = "📋 <b>Очередь постов:</b>\n\n"
        
        for i, queued_post in enumerate(queue[:20], 1):  # Show first 20
            post = queued_post.post
            text += f"{i}. <b>ID:</b> <code>{post.id[:8]}</code>\n"
            text += f"   Канал: <code>{post.channel_id}</code>\n"
            text += f"   Статус: {post.status}\n"
            text += f"   Тема: {post.theme or 'Не указана'}\n"
            text += f"   Приоритет: {post.priority}\n"
            if post.created_at:
                text += f"   Создан: {post.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            text += "\n"
        
        if len(queue) > 20:
            text += f"... и еще {len(queue) - 20} постов"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to get queue: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def autopost_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add posting schedule.
    
    Usage: /autopost_schedule <channel_id> <time_slots>
    Example: /autopost_schedule -1001234567890 09:00,15:00,21:0
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_schedule <channel_id> <time_slots>\n"
            "Пример: /autopost_schedule -1001234567890 09:00,15:00,21:0\n"
            "Формат времени: ЧЧ:ММ (24-часовой формат)"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -100 (публичный) или - (приватный)"
            )
            return
        
        channel_id = int(channel_id_str)
        time_slots_str = context.args[1]
        
        is_valid, time_slots = validate_time_slots(time_slots_str)
        if not is_valid:
            await update.message.reply_text(
                "❌ Неверный формат времени!\n"
                "Используйте формат: ЧЧ:ММ,Ч:М,Ч:ММ\n"
                "Пример: 09:00,15:00,21:0"
            )
            return
        
        if len(time_slots) > 24:
            await update.message.reply_text("❌ Слишком много временных слотов (максимум 24)")
            return
        
        # Get channel manager to check if channel exists
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        channel = await channel_manager.get_channel(channel_id)
        if not channel:
            await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе автопостинга")
            return
        
        # Create schedule
        scheduler = AutoPostScheduler()
        schedule_config = ScheduleConfig(
            channel_id=channel_id,
            mode=ScheduleMode.FIXED,
            time_slots=time_slots,
            days_of_week=list(range(7))  # All days
        )
        
        schedule_id = await scheduler.add_schedule(channel_id, schedule_config)
        
        await update.message.reply_text(
            f"✅ Расписание добавлено!\n\n"
            f"ID: <code>{schedule_id[:8]}</code>\n"
            f"Канал: <code>{channel_id}</code>\n"
            f"Время публикаций: {', '.join(time_slots)}\n"
            f"Дни недели: все",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Failed to add schedule: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def autopost_list_schedules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List posting schedules.
    
    Usage: /autopost_list_schedules [channel_id]
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    try:
        channel_id = None
        if context.args:
            channel_id_str = context.args[0]
            if not validate_channel_id(channel_id_str):
                await update.message.reply_text(
                    "❌ Неверный формат ID канала!\n"
                    "ID канала должен начинаться с -100 (публичный) или - (приватный)"
                )
                return
            channel_id = int(channel_id_str)
        
        # Import here to avoid circular import
        from sqlalchemy import select
        from src.models.autopost import AutoPostSchedule
        from src.database.autopost_db import autopost_db
        
        async with autopost_db.session() as session:
            query = select(AutoPostSchedule).where(AutoPostSchedule.is_active == True)
            if channel_id:
                query = query.where(AutoPostSchedule.channel_id == channel_id)
            
            result = await session.execute(query)
            schedules = result.scalars().all()
        
        if not schedules:
            if channel_id:
                await update.message.reply_text(f"📋 Нет активных расписаний для канала {channel_id}")
            else:
                await update.message.reply_text("📋 Нет активных расписаний")
            return
        
        text = "📋 <b>Активные расписания:</b>\n\n"
        
        for i, schedule in enumerate(schedules, 1):
            config = schedule.config
            text += f"{i}. <b>ID:</b> <code>{schedule.id[:8]}</code>\n"
            text += f"   Канал: <code>{schedule.channel_id}</code>\n"
            text += f"   Режим: {config['mode']}\n"
            text += f"   Время: {', '.join(config['time_slots'])}\n"
            if schedule.next_run:
                text += f"   Следующая публикация: {schedule.next_run.strftime('%Y-%m-%d %H:%M')}\n"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def autopost_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show auto-posting help.
    
    Usage: /autopost_help
    """
    help_text = """
 📚 <b>Команды автопостинга:</b>

 <b>Управление каналами:</b>
 • /autopost_add_channel - Добавить канал
 • /autopost_remove_channel - Удалить канал
 • /autopost_list_channels - Список каналов
 • /autopost_stats - Статистика

 <b>Генерация контента:</b>
 • /autopost_generate - Сгенерировать пост
 • /autopost_approve - Одобрить пост
 • /autopost_queue - Просмотр очереди

 <b>Расписание:</b>
 • /autopost_schedule - Добавить расписание
 • /autopost_list_schedules - Список расписаний

 <b>Аналитика:</b>
 • /autopost_analytics - Аналитика канала
 • /autopost_trends - Тренды канала

 <b>Настройки:</b>
 • /autopost_set_moderation - Включить/отключить модерацию
 • /autopost_set_frequency - Установить частоту публикаций

 <b>Справка:</b>
 • /autopost_help - Эта справка
     """
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def autopost_set_moderation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/disable moderation for a channel.
    
    Usage: /autopost_set_moderation <channel_id> <on|off>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_set_moderation <channel_id> <on|off>\n"
            "Пример: /autopost_set_moderation -1001234567890 on"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -100 (публичный) или - (приватный)"
            )
            return
        
        channel_id = int(channel_id_str)
        action = context.args[1].lower()
        
        if action not in ['on', 'off']:
            await update.message.reply_text("❌ Неверное значение. Используйте 'on' или 'off'")
            return
        
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        
        channel = await channel_manager.get_channel(channel_id)
        if not channel:
            await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе")
            return
        
        # Update channel settings
        settings = channel.settings or {}
        settings['require_moderation'] = action == 'on'
        
        await channel_manager.update_channel_settings(channel_id, settings)
        
        status = "включена" if action == 'on' else "отключена"
        await update.message.reply_text(
            f"✅ Модерация для канала {channel_id} {status}\n"
            f"Все новые посты теперь будут требовать одобрения"
        )
        
    except Exception as e:
        logger.error(f"Failed to set moderation: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка установки модерации: {e}")


async def autopost_set_frequency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set posting frequency for a channel.
    
    Usage: /autopost_set_frequency <channel_id> <frequency>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_set_frequency <channel_id> <frequency>\n"
            "Пример: /autopost_set_frequency -1001234567890 5\n"
            "Частота указывается в постах в день (1-24)"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -10 (публичный) или - (приватный)"
            )
            return
        
        channel_id = int(channel_id_str)
        frequency_str = context.args[1]
        
        is_valid_freq, frequency = validate_frequency(frequency_str)
        if not is_valid_freq:
            await update.message.reply_text("❌ Неверная частота публикаций (1-24 постов в день)")
            return
        
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        
        channel = await channel_manager.get_channel(channel_id)
        if not channel:
            await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе")
            return
        
        # Update channel settings
        settings = channel.settings or {}
        settings['post_frequency'] = frequency
        
        await channel_manager.update_channel_settings(channel_id, settings)
        
        await update.message.reply_text(
            f"✅ Частота публикаций для канала {channel_id} установлена на {frequency} постов/день"
        )
        
    except Exception as e:
        logger.error(f"Failed to set frequency: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка установки частоты: {e}")


async def autopost_analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get analytics for a channel.
    
    Usage: /autopost_analytics <channel_id>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_analytics <channel_id>\n"
            "Пример: /autopost_analytics -1001234567890"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -100 (публичный) или - (приватный)"
            )
            return
        
        channel_id = int(channel_id_str)
        
        # Validate channel_id range
        if abs(channel_id) < 1000:
            await update.message.reply_text("❌ Неверный ID канала")
            return
        
        # Get channel manager to check if channel exists
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        channel = await channel_manager.get_channel(channel_id)
        if not channel:
            await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе автопостинга")
            return
        
        # Initialize analytics connector
        analytics_connector = TelegramAnalyticsConnector(bot)
        
        # Get analytics data
        analytics_data = await analytics_connector.get_channel_analytics(channel_id)
        
        if not analytics_data:
            await update.message.reply_text(f"📊 Нет аналитических данных для канала {channel_id}")
            return
        
        # Format analytics response
        text = f"📊 <b>Аналитика для канала {channel.name}</b>\n\n"
        text += f"ID: <code>{channel_id}</code>\n\n"
        
        # Engagement metrics
        engagement = analytics_data.get('engagement', {})
        text += "<b>Вовлеченность:</b>\n"
        text += f"• Просмотры: {engagement.get('views', 0)}\n"
        text += f"• Лайки: {engagement.get('likes', 0)}\n"
        text += f"• Комментарии: {engagement.get('comments', 0)}\n"
        text += f"• Репосты: {engagement.get('forwards', 0)}\n"
        text += f"• Сохранения: {engagement.get('saves', 0)}\n\n"
        
        # Performance metrics
        performance = analytics_data.get('performance', {})
        text += "<b>Производительность:</b>\n"
        text += f"• Постов за 24ч: {performance.get('posts_24h', 0)}\n"
        text += f"• Среднее время ответа: {format_duration(performance.get('avg_response_time', 0))}\n"
        text += f"• Пик активности: {performance.get('peak_activity', 'Неизвестно')}\n\n"
        
        # Growth metrics
        growth = analytics_data.get('growth', {})
        text += "<b>Рост:</b>\n"
        text += f"• Подписчики: {growth.get('subscribers', 0)}\n"
        text += f"• Новые подписчики (24ч): {growth.get('new_subscribers_24h', 0)}\n"
        text += f"• Отписки (24ч): {growth.get('unsubscribes_24h', 0)}\n"
        text += f"• Прирост: {growth.get('net_growth', 0)}\n\n"
        
        # Engagement rate
        engagement_rate = engagement.get('engagement_rate', 0)
        text += f"<b>Уровень вовлеченности:</b> {engagement_rate:.2f}%\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка получения аналитики: {str(e)[:200]}...")


async def autopost_trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get trending topics for a channel.
    
    Usage: /autopost_trends <channel_id>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Неверное количество аргументов!\n\n"
            "Использование: /autopost_trends <channel_id>\n"
            "Пример: /autopost_trends -1001234567890"
        )
        return
    
    try:
        channel_id_str = context.args[0]
        if not validate_channel_id(channel_id_str):
            await update.message.reply_text(
                "❌ Неверный формат ID канала!\n"
                "ID канала должен начинаться с -100 (публичный) или - (приватный)"
            )
            return
        
        channel_id = int(channel_id_str)
        
        # Validate channel_id range
        if abs(channel_id) < 10000:
            await update.message.reply_text("❌ Неверный ID канала")
            return
        
        # Get channel manager to check if channel exists
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        channel = await channel_manager.get_channel(channel_id)
        if not channel:
            await update.message.reply_text(f"❌ Канал {channel_id} не найден в системе автопостинга")
            return
        
        # Initialize analytics connector
        analytics_connector = TelegramAnalyticsConnector(bot)
        
        # Get trending topics
        trends_data = await analytics_connector.get_channel_trends(channel_id)
        
        if not trends_data:
            await update.message.reply_text(f"📈 Нет данных о трендах для канала {channel_id}")
            return
        
        # Format trends response
        text = f"📈 <b>Тренды для канала {channel.name}</b>\n\n"
        text += f"ID: <code>{channel_id}</code>\n\n"
        
        # Trending topics
        trending_topics = trends_data.get('trending_topics', [])
        if trending_topics:
            text += "<b>Популярные темы:</b>\n"
            for i, topic in enumerate(trending_topics[:10], 1):  # Top 10 topics
                text += f"{i}. {topic.get('name', 'Неизвестно')} - {topic.get('mentions', 0)} упоминаний\n"
            text += "\n"
        
        # Trending hashtags
        trending_hashtags = trends_data.get('trending_hashtags', [])
        if trending_hashtags:
            text += "<b>Популярные хэштеги:</b>\n"
            for i, hashtag in enumerate(trending_hashtags[:10], 1):  # Top 10 hashtags
                text += f"{i}. #{hashtag.get('name', 'Неизвестно')} - {hashtag.get('mentions', 0)} упоминаний\n"
            text += "\n"
        
        # Trending content types
        content_types = trends_data.get('content_types', {})
        if content_types:
            text += "<b>Типы контента:</b>\n"
            for content_type, count in content_types.items():
                text += f"• {content_type}: {count}\n"
            text += "\n"
        
        # Peak activity times
        peak_times = trends_data.get('peak_activity_times', [])
        if peak_times:
            text += "<b>Пиковые часы активности:</b>\n"
            for time_range in peak_times[:5]:  # Top 5 time ranges
                text += f"• {time_range}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to get trends: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка получения трендов: {str(e)[:200]}...")
]]>