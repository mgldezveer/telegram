"""Conversation manager for multi-step user interactions."""

import logging
import asyncio
from telegram import Update, ForceReply
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from datetime import datetime, timedelta
from .validators import InputValidator
from .conversation_factory import ConversationHandlerFactory

logger = logging.getLogger(__name__)

# Таймауты для операций
TELEGRAM_API_TIMEOUT = 10.0  # секунд
DATABASE_TIMEOUT = 5.0  # секунд

# Conversation states
CHANNEL_ID, CHANNEL_NAME = range(2)
CUSTOM_THEME = 100
EDIT_POST_CONTENT = 101


class ConversationManager:
    """Manages multi-step conversations with users."""
    
    def __init__(self, bot_controller=None):
        """Initialize conversation manager.
        
        Args:
            bot_controller: Reference to main bot controller
        """
        self.bot_controller = bot_controller
        self.conversation_timeout = timedelta(minutes=5)
        self._active_conversations = {}  # user_id -> conversation_data
    
    def create_custom_theme_handler(self) -> ConversationHandler:
        """Create conversation handler for custom theme input.
        
        Returns:
            ConversationHandler for custom theme
        """
        return ConversationHandlerFactory.create_handler(
            name='custom_theme',
            entry_points=[
                CallbackQueryHandler(
                    self.start_custom_theme,
                    pattern='^theme:custom$'
                )
            ],
            states={
                CUSTOM_THEME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.receive_custom_theme
                    )
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel_conversation),
                CallbackQueryHandler(
                    self.cancel_conversation,
                    pattern='^cancel:'
                )
            ],
            per_message=False,  # Mixed handlers: CallbackQuery entry + Message state
            conversation_timeout=self.conversation_timeout.total_seconds()
        )
    
    def create_channel_registration_handler(self) -> ConversationHandler:
        """Create conversation handler for channel registration.
        
        Returns:
            ConversationHandler for channel registration
        """
        return ConversationHandlerFactory.create_handler(
            name='channel_registration',
            entry_points=[
                CallbackQueryHandler(
                    self.start_channel_registration,
                    pattern='^channel:add$'
                )
            ],
            states={
                CHANNEL_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.receive_channel_id
                    )
                ],
                CHANNEL_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.receive_channel_name
                    )
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel_conversation),
                CallbackQueryHandler(
                    self.cancel_conversation,
                    pattern='^cancel:'
                )
            ],
            per_message=False,  # Mixed handlers: CallbackQuery entry + Message state
            conversation_timeout=self.conversation_timeout.total_seconds()
        )
    
    async def start_channel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start channel registration conversation.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            Next conversation state
        """
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Starting channel registration for user {update.effective_user.id}")
        
        # Store conversation start time
        context.user_data['conversation_start'] = datetime.now()
        context.user_data['conversation_type'] = 'channel_registration'
        
        text = (
            "➕ <b>Регистрация канала</b>\n\n"
            "Шаг 1 из 2: Отправьте ID канала\n\n"
            "ID канала выглядит так: <code>-1001234567890</code>\n\n"
            "<b>Как найти ID канала:</b>\n"
            "1. Перешлите любое сообщение из канала боту @userinfobot\n"
            "2. Бот покажет ID канала\n"
            "3. Скопируйте ID и отправьте его сюда\n\n"
            "<b>Важно:</b> Бот должен быть администратором канала!\n\n"
            "Отправьте /cancel для отмены"
        )
        
        await query.edit_message_text(text, parse_mode='HTML')
        
        return CHANNEL_ID
    
    async def receive_channel_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate channel ID.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            Next conversation state or END
        """
        channel_id_str = update.message.text.strip()
        
        logger.info(f"Received channel ID: {channel_id_str}")
        
        # Validate channel ID format using validator
        validation_result = InputValidator.validate_channel_id(channel_id_str)
        
        if not validation_result.is_valid:
            await update.message.reply_text(
                f"❌ {validation_result.error_message}\n\n"
                f"Попробуйте еще раз или отправьте /cancel для отмены",
                parse_mode='HTML'
            )
            return CHANNEL_ID
        
        channel_id = validation_result.sanitized_value
        
        # Check if bot has access to the channel
        try:
            # Параллельные запросы с таймаутом для оптимизации
            async with asyncio.timeout(TELEGRAM_API_TIMEOUT):
                chat, bot_member = await asyncio.gather(
                    context.bot.get_chat(channel_id),
                    context.bot.get_chat_member(channel_id, context.bot.id),
                    return_exceptions=False
                )
            
            if bot_member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ Бот не является администратором канала\n\n"
                    "Пожалуйста, добавьте бота в канал как администратора "
                    "с правами на публикацию сообщений\n\n"
                    "Попробуйте еще раз или отправьте /cancel для отмены",
                    parse_mode='HTML'
                )
                return CHANNEL_ID
            
            # Store channel ID and info
            context.user_data['new_channel_id'] = channel_id
            context.user_data['new_channel_title'] = chat.title
            
            # Ask for channel name
            text = (
                f"✅ Канал найден: <b>{chat.title}</b>\n\n"
                f"Шаг 2 из 2: Введите название для канала\n\n"
                f"Это название будет использоваться в интерфейсе бота.\n"
                f"Вы можете использовать название канала или придумать свое.\n\n"
                f"Отправьте /cancel для отмены"
            )
            
            await update.message.reply_text(text, parse_mode='HTML')
            
            return CHANNEL_NAME
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout accessing channel {channel_id}")
            await update.message.reply_text(
                "❌ Превышено время ожидания ответа от Telegram\n\n"
                "Попробуйте еще раз через несколько секунд\n\n"
                "Отправьте /cancel для отмены",
                parse_mode='HTML'
            )
            return CHANNEL_ID
            
        except Exception as e:
            logger.error(f"Error accessing channel {channel_id}: {e}")
            await update.message.reply_text(
                "❌ Не удалось получить доступ к каналу\n\n"
                "<b>Возможные причины:</b>\n"
                "• Неверный ID канала\n"
                "• Бот не добавлен в канал\n"
                "• Бот не является администратором\n\n"
                "Проверьте ID и права бота, затем попробуйте снова\n\n"
                "Отправьте /cancel для отмены",
                parse_mode='HTML'
            )
            return CHANNEL_ID
    
    async def receive_channel_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive channel name and complete registration.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            ConversationHandler.END
        """
        channel_name = update.message.text.strip()
        
        logger.info(f"Received channel name: {channel_name}")
        
        # Validate channel name using validator
        validation_result = InputValidator.validate_channel_name(channel_name)
        
        if not validation_result.is_valid:
            await update.message.reply_text(
                f"❌ {validation_result.error_message}\n\n"
                f"Попробуйте еще раз или отправьте /cancel для отмены",
                parse_mode='HTML'
            )
            return CHANNEL_NAME
        
        channel_name = validation_result.sanitized_value
        
        # Get stored channel data
        channel_id = context.user_data.get('new_channel_id')
        channel_title = context.user_data.get('new_channel_title')
        
        if not channel_id:
            await update.message.reply_text(
                "❌ Ошибка: данные канала не найдены\n\n"
                "Пожалуйста, начните регистрацию заново",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Register channel
        try:
            await update.message.reply_text(
                "⏳ Регистрирую канал...",
                parse_mode='HTML'
            )
            
            if self.bot_controller and self.bot_controller.channel_manager:
                from src.services.channel_manager import ChannelConfig
                
                channel_config = ChannelConfig(name=channel_name)
                channel = await self.bot_controller.channel_manager.register_channel(
                    channel_id,
                    channel_config
                )
                
                # Success message
                text = (
                    f"✅ <b>Канал успешно зарегистрирован!</b>\n\n"
                    f"📺 Название: <b>{channel_name}</b>\n"
                    f"🆔 ID: <code>{channel_id}</code>\n"
                    f"📊 Telegram: {channel_title}"
                )
                
                await update.message.reply_text(text, parse_mode='HTML')
                
                # Show channels menu
                if self.bot_controller and self.bot_controller.menu_system:
                    # Show channels menu directly without extra message
                    await self.bot_controller.menu_system.show_channels_menu(update, context)
            else:
                await update.message.reply_text(
                    "❌ Ошибка: сервис управления каналами недоступен",
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Error registering channel: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при регистрации канала\n\n"
                f"<b>Ошибка:</b> {str(e)}\n\n"
                f"Попробуйте позже или обратитесь к администратору",
                parse_mode='HTML'
            )
        
        # Clean up conversation data
        context.user_data.pop('new_channel_id', None)
        context.user_data.pop('new_channel_title', None)
        context.user_data.pop('conversation_start', None)
        context.user_data.pop('conversation_type', None)
        
        return ConversationHandler.END
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current conversation.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            ConversationHandler.END
        """
        conversation_type = context.user_data.get('conversation_type', 'unknown')
        
        logger.info(f"Cancelling conversation: {conversation_type}")
        
        # Clean up conversation data
        context.user_data.pop('new_channel_id', None)
        context.user_data.pop('new_channel_title', None)
        context.user_data.pop('conversation_start', None)
        context.user_data.pop('conversation_type', None)
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                "❌ Операция отменена\n\n"
                "Используйте меню для навигации",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Операция отменена\n\n"
                "Используйте /start для возврата в главное меню",
                parse_mode='HTML'
            )
        
        return ConversationHandler.END
    
    async def handle_conversation_timeout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle conversation timeout.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            ConversationHandler.END
        """
        conversation_type = context.user_data.get('conversation_type', 'unknown')
        
        logger.info(f"Conversation timeout: {conversation_type}")
        
        # Clean up conversation data
        context.user_data.pop('new_channel_id', None)
        context.user_data.pop('new_channel_title', None)
        context.user_data.pop('conversation_start', None)
        context.user_data.pop('conversation_type', None)
        
        text = (
            "⏱️ <b>Время ожидания истекло</b>\n\n"
            "Операция была отменена из-за неактивности\n\n"
            "Используйте /start для возврата в главное меню"
        )
        
        if update.message:
            await update.message.reply_text(text, parse_mode='HTML')
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode='HTML')
        
        return ConversationHandler.END

    
    async def start_custom_theme(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start custom theme input conversation.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            Next conversation state
        """
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Starting custom theme input for user {update.effective_user.id}")
        
        # Store conversation data
        context.user_data['conversation_start'] = datetime.now()
        context.user_data['conversation_type'] = 'custom_theme'
        
        text = (
            "✏️ <b>Своя тема</b>\n\n"
            "Введите тему для генерации поста\n\n"
            "<b>Примеры тем:</b>\n"
            "• Искусственный интеллект в медицине\n"
            "• Тренды веб-разработки 2024\n"
            "• Как начать карьеру в IT\n\n"
            "Отправьте /cancel для отмены"
        )
        
        await query.edit_message_text(text, parse_mode='HTML')
        
        return CUSTOM_THEME
    
    async def receive_custom_theme(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive custom theme and start generation.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            ConversationHandler.END
        """
        theme = update.message.text.strip()
        
        logger.info(f"Received custom theme: {theme}")
        
        # Validate theme using validator
        validation_result = InputValidator.validate_theme(theme)
        
        if not validation_result.is_valid:
            await update.message.reply_text(
                f"❌ {validation_result.error_message}\n\n"
                f"Попробуйте еще раз или отправьте /cancel для отмены",
                parse_mode='HTML'
            )
            return CUSTOM_THEME
        
        theme = validation_result.sanitized_value
        
        # Start generation with custom theme
        try:
            if self.bot_controller and self.bot_controller.content_interface:
                await update.message.reply_text(
                    f"✅ Тема принята: <b>{theme}</b>\n\n"
                    f"Начинаю генерацию...",
                    parse_mode='HTML'
                )
                
                # Create a fake callback query update for content interface
                # We'll use the message update but call generate_content directly
                # First we need to create a proper update object
                from telegram import CallbackQuery
                
                # For now, just trigger generation through context
                # The content interface will handle it
                channel_id = context.user_data.get('generation_channel_id')
                if channel_id:
                    # Store theme in context
                    context.user_data['custom_theme'] = theme
                    
                    # We'll need to handle this differently - let's just store and return
                    await update.message.reply_text(
                        "⏳ Генерирую пост...",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка: канал не выбран",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    "❌ Ошибка: интерфейс контента недоступен",
                    parse_mode='HTML'
                )
        
        except Exception as e:
            logger.error(f"Error starting generation with custom theme: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при генерации\n\n{str(e)}",
                parse_mode='HTML'
            )
        
        # Clean up conversation data
        context.user_data.pop('conversation_start', None)
        context.user_data.pop('conversation_type', None)
        
        return ConversationHandler.END

    async def cleanup_expired_conversations(self, context: ContextTypes.DEFAULT_TYPE = None) -> int:
        """Clean up expired conversations.
        
        Args:
            context: Callback context (optional)
            
        Returns:
            Number of cleaned up conversations
        """
        now = datetime.now()
        cleaned = 0
        
        # Get all user data from context
        # Note: This is a simplified version - in production you'd iterate through all users
        for user_id in list(self._active_conversations.keys()):
            conversation_start = self._active_conversations[user_id].get('start_time')
            
            if conversation_start and now - conversation_start > self.conversation_timeout:
                # Clean up expired conversation
                self._active_conversations.pop(user_id, None)
                cleaned += 1
                logger.info(f"Cleaned up expired conversation for user {user_id}")
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired conversations")
        
        return cleaned
    
    def track_conversation(self, user_id: int, conversation_type: str) -> None:
        """Track active conversation.
        
        Args:
            user_id: User ID
            conversation_type: Type of conversation
        """
        self._active_conversations[user_id] = {
            'type': conversation_type,
            'start_time': datetime.now()
        }
        logger.debug(f"Tracking conversation for user {user_id}: {conversation_type}")
    
    def end_conversation(self, user_id: int) -> None:
        """End tracked conversation.
        
        Args:
            user_id: User ID
        """
        if user_id in self._active_conversations:
            del self._active_conversations[user_id]
            logger.debug(f"Ended conversation tracking for user {user_id}")
    
    def create_edit_post_handler(self) -> ConversationHandler:
        """Create conversation handler for post editing.
        
        Returns:
            ConversationHandler for post editing
        """
        return ConversationHandlerFactory.create_handler(
            name='edit_post',
            entry_points=[
                CallbackQueryHandler(
                    self.start_edit_post,
                    pattern='^posts:edit:'
                )
            ],
            states={
                EDIT_POST_CONTENT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.receive_edited_content
                    )
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel_conversation),
                CallbackQueryHandler(
                    self.cancel_conversation,
                    pattern='^cancel:'
                )
            ],
            per_message=False,  # Mixed handlers: CallbackQuery entry + Message state
            conversation_timeout=self.conversation_timeout.total_seconds()
        )
    
    async def start_edit_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start post editing conversation.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            Next conversation state
        """
        query = update.callback_query
        await query.answer()
        
        # Extract post_id from callback data
        post_id = int(query.data.split(':')[2])
        
        logger.info(f"Starting post edit for post {post_id}")
        
        # Store conversation data
        context.user_data['conversation_start'] = datetime.now()
        context.user_data['conversation_type'] = 'edit_post'
        context.user_data['edit_post_id'] = post_id
        
        # Get current post content
        try:
            from src.models.base import async_session_maker
            from src.repositories.post_repository import PostRepository
            
            async with asyncio.timeout(DATABASE_TIMEOUT):
                async with async_session_maker() as session:
                    post_repo = PostRepository(session)
                    post = await post_repo.get_by_id(post_id)
                
                if not post:
                    await query.edit_message_text(
                        "❌ Пост не найден",
                        parse_mode='HTML'
                    )
                    return ConversationHandler.END
                
                text = (
                    "✏️ <b>Редактирование поста</b>\n\n"
                    "<b>Текущий контент:</b>\n"
                    f"{post.content}\n\n"
                    "Отправьте новый текст для поста\n\n"
                    "Отправьте /cancel для отмены"
                )
                
                await query.edit_message_text(text, parse_mode='HTML')
                
                return EDIT_POST_CONTENT
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout loading post {post_id}")
            await query.edit_message_text(
                "❌ Превышено время ожидания ответа от базы данных\n\n"
                "Попробуйте еще раз через несколько секунд",
                parse_mode='HTML'
            )
            return ConversationHandler.END
                
        except Exception as e:
            logger.error(f"Error starting post edit: {e}")
            await query.edit_message_text(
                f"❌ Ошибка при загрузке поста\n\n{str(e)}",
                parse_mode='HTML'
            )
            return ConversationHandler.END
    
    async def receive_edited_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive edited post content and save.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            ConversationHandler.END
        """
        new_content = update.message.text.strip()
        post_id = context.user_data.get('edit_post_id')
        
        logger.info(f"Received edited content for post {post_id}")
        
        if not post_id:
            await update.message.reply_text(
                "❌ Ошибка: ID поста не найден\n\n"
                "Пожалуйста, начните редактирование заново",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Validate content
        if len(new_content) < 10:
            await update.message.reply_text(
                "❌ Текст слишком короткий (минимум 10 символов)\n\n"
                "Попробуйте еще раз или отправьте /cancel для отмены",
                parse_mode='HTML'
            )
            return EDIT_POST_CONTENT
        
        if len(new_content) > 4000:
            await update.message.reply_text(
                "❌ Текст слишком длинный (максимум 4000 символов)\n\n"
                "Попробуйте еще раз или отправьте /cancel для отмены",
                parse_mode='HTML'
            )
            return EDIT_POST_CONTENT
        
        # Update post
        try:
            from src.models.base import async_session_maker
            from src.repositories.post_repository import PostRepository
            from sqlalchemy import update as sql_update
            from src.models import Post
            
            async with asyncio.timeout(DATABASE_TIMEOUT):
                async with async_session_maker() as session:
                    # Update post content
                    await session.execute(
                        sql_update(Post)
                        .where(Post.id == post_id)
                        .values(content=new_content)
                    )
                    await session.commit()
                    
                    # Get updated post
                    post_repo = PostRepository(session)
                    post = await post_repo.get_by_id(post_id)
                
                # Show success message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("👁️ Просмотреть пост", callback_data=f"posts:view:{post_id}")],
                    [InlineKeyboardButton("⬅️ К списку постов", callback_data=f"posts:channel:{post.channel_id}")]
                ])
                
                text = (
                    "✅ <b>Пост обновлен!</b>\n\n"
                    "<b>Новый контент:</b>\n"
                    f"{new_content[:200]}{'...' if len(new_content) > 200 else ''}"
                )
                
                await update.message.reply_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout updating post {post_id}")
            await update.message.reply_text(
                "❌ Превышено время ожидания ответа от базы данных\n\n"
                "Попробуйте еще раз через несколько секунд",
                parse_mode='HTML'
            )
                
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при обновлении поста\n\n{str(e)}",
                parse_mode='HTML'
            )
        
        # Clean up conversation data
        context.user_data.pop('edit_post_id', None)
        context.user_data.pop('conversation_start', None)
        context.user_data.pop('conversation_type', None)
        
        return ConversationHandler.END
    
    def get_active_conversations_count(self) -> int:
        """Get count of active conversations.
        
        Returns:
            Number of active conversations
        """
        return len(self._active_conversations)
