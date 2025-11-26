"""Auto-posting bot commands."""

import logging
from telegram import Update
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
from src.models.autopost import ScheduleMode

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in config.bot.admin_ids


async def autopost_add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add channel for auto-posting.
    
    Usage: /autopost_add_channel <channel_id> <name>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /autopost_add_channel <channel_id> <name>\n"
            "Пример: /autopost_add_channel -1001234567890 'Мой канал'"
        )
        return
    
    try:
        channel_id = int(context.args[0])
        channel_name = " ".join(context.args[1:])
        
        # Get channel manager from bot_data
        bot = context.bot
        channel_manager = AutoPostChannelManager(bot)
        
        # Add channel
        config_obj = ChannelConfig(name=channel_name)
        channel = await channel_manager.add_channel(channel_id, config_obj)
        
        await update.message.reply_text(
            f"✅ Канал добавлен для автопостинга!\n\n"
            f"ID: {channel.id}\n"
            f"Название: {channel.name}\n"
            f"Статус: {'Активен' if channel.is_active else 'Неактивен'}"
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    except Exception as e:
        logger.error(f"Failed to add channel: {e}")
        await update.message.reply_text(f"❌ Ошибка при добавлении канала: {e}")


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
        
        for channel in channels:
            settings = channel.settings or {}
            text += f"<b>{channel.name}</b>\n"
            text += f"ID: <code>{channel.id}</code>\n"
            text += f"Частота: {settings.get('post_frequency', 3)} постов/день\n"
            text += f"Автопубликация: {'Да' if settings.get('auto_publish', True) else 'Нет'}\n"
            text += f"Модерация: {'Да' if settings.get('require_moderation', False) else 'Нет'}\n"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to list channels: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def autopost_generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate post for auto-posting.
    
    Usage: /autopost_generate <channel_id> <theme>
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /autopost_generate <channel_id> <theme>\n"
            "Пример: /autopost_generate -1001234567890 технологии"
        )
        return
    
    try:
        channel_id = int(context.args[0])
        theme = " ".join(context.args[1:])
        
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
        preview += f"ID: <code>{queue_id}</code>\n"
        preview += f"Канал: {channel_id}\n"
        preview += f"Тема: {theme}\n\n"
        preview += f"<b>Контент:</b>\n{post.content[:500]}"
        
        if len(post.content) > 500:
            preview += "..."
        
        await update.message.reply_text(preview, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to generate post: {e}")
        await update.message.reply_text(f"❌ Ошибка генерации: {e}")


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
            channel_id = int(context.args[0])
        
        queue_manager = AutoPostQueueManager()
        queue = await queue_manager.get_queue(channel_id=channel_id)
        
        if not queue:
            await update.message.reply_text("📋 Очередь постов пуста")
            return
        
        text = "📋 <b>Очередь постов:</b>\n\n"
        
        for i, queued_post in enumerate(queue[:10], 1):  # Show first 10
            post = queued_post.post
            text += f"{i}. <b>ID:</b> <code>{post.id[:8]}</code>\n"
            text += f"   Канал: {post.channel_id}\n"
            text += f"   Статус: {post.status}\n"
            text += f"   Тема: {post.theme or 'Не указана'}\n"
            text += f"   Приоритет: {post.priority}\n\n"
        
        if len(queue) > 10:
            text += f"... и еще {len(queue) - 10} постов"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Failed to get queue: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def autopost_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add posting schedule.
    
    Usage: /autopost_schedule <channel_id> <time_slots>
    Example: /autopost_schedule -1001234567890 09:00,15:00,21:00
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только для администраторов")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /autopost_schedule <channel_id> <time_slots>\n"
            "Пример: /autopost_schedule -1001234567890 09:00,15:00,21:00"
        )
        return
    
    try:
        channel_id = int(context.args[0])
        time_slots = context.args[1].split(',')
        
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
            f"ID: <code>{schedule_id}</code>\n"
            f"Канал: {channel_id}\n"
            f"Время публикаций: {', '.join(time_slots)}",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Failed to add schedule: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def autopost_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show auto-posting help.
    
    Usage: /autopost_help
    """
    help_text = """
📚 <b>Команды автопостинга:</b>

<b>Управление каналами:</b>
/autopost_add_channel - Добавить канал
/autopost_list_channels - Список каналов
/autopost_remove_channel - Удалить канал

<b>Генерация контента:</b>
/autopost_generate - Сгенерировать пост
/autopost_queue - Просмотр очереди
/autopost_approve - Одобрить пост

<b>Расписание:</b>
/autopost_schedule - Добавить расписание
/autopost_list_schedules - Список расписаний

<b>Справка:</b>
/autopost_help - Эта справка
    """
    
    await update.message.reply_text(help_text, parse_mode='HTML')
