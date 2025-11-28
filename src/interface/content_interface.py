"""Content management interface."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .keyboard_builder import KeyboardBuilder
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class ContentInterface:
    """Interface for content generation and management."""
    
    def __init__(self, bot_controller=None):
        """Initialize content interface.
        
        Args:
            bot_controller: Reference to main bot controller
        """
        self.keyboard_builder = KeyboardBuilder()
        self.formatter = MessageFormatter()
        self.bot_controller = bot_controller
    
    async def show_channel_selection_for_generation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show channel selection for content generation.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info(f"Showing channel selection for generation to user {update.effective_user.id}")
        
        try:
            # Get channels
            channels = []
            if self.bot_controller and self.bot_controller.channel_manager:
                channels = await self.bot_controller.channel_manager.get_all_channels()
            
            if not channels:
                text = (
                    "✍️ <b>Генерация контента</b>\n\n"
                    "<i>У вас нет зарегистрированных каналов</i>\n\n"
                    "Сначала добавьте канал в разделе <b>Каналы</b>"
                )
                keyboard = self.keyboard_builder.build_back_button("menu:content")
            else:
                text = (
                    "✍️ <b>Генерация контента</b>\n\n"
                    "Выберите канал для создания поста:"
                )
                
                # Build channel selection keyboard
                keyboard_buttons = []
                for channel in channels:
                    # Support both dict and object
                    channel_name = channel.get('name') if isinstance(channel, dict) else channel.name
                    channel_id = channel.get('channel_id') if isinstance(channel, dict) else channel.id
                    
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            f"📺 {channel_name}",
                            callback_data=f"generate:{channel_id}"
                        )
                    ])
                
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        "⬅️ Назад",
                        callback_data="menu:content"
                    )
                ])
                
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing channel selection: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка загрузки списка каналов\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def show_theme_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Show theme selection for content generation.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Showing theme selection for channel {channel_id}")
        
        try:
            # Get channel info
            channel = await self._get_channel(channel_id)
            
            if not channel:
                await update.callback_query.edit_message_text(
                    "❌ Канал не найден",
                    parse_mode='HTML'
                )
                return
            
            # Store channel ID for generation
            context.user_data['generation_channel_id'] = channel_id
            
            # Support both dict and object
            channel_name = channel.get('name') if isinstance(channel, dict) else channel.name
            
            text = (
                f"✍️ <b>Генерация контента</b>\n\n"
                f"Канал: <b>{channel_name}</b>\n\n"
                f"Выберите тему для поста:"
            )
            
            keyboard = self.keyboard_builder.build_theme_selection()
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing theme selection: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при выборе темы\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def generate_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, theme: str):
        """Generate content with selected theme.
        
        Args:
            update: Telegram update
            context: Callback context
            theme: Theme for content generation
        """
        channel_id = context.user_data.get('generation_channel_id')
        
        if not channel_id:
            await update.callback_query.edit_message_text(
                "❌ Ошибка: канал не выбран\n\n"
                "Пожалуйста, начните генерацию заново",
                parse_mode='HTML'
            )
            return
        
        logger.info(f"Generating content for channel {channel_id}, theme: {theme}")
        
        try:
            # Get channel info
            channel = await self._get_channel(channel_id)
            
            if not channel:
                await update.callback_query.edit_message_text(
                    "❌ Канал не найден",
                    parse_mode='HTML'
                )
                return
            
            # Show loading message
            await update.callback_query.edit_message_text(
                f"⏳ Генерирую пост на тему <b>{theme}</b>...\n\n"
                f"Это может занять несколько секунд",
                parse_mode='HTML'
            )
            
            # Send typing action
            from telegram.constants import ChatAction
            await update.callback_query.message.chat.send_action(ChatAction.TYPING)
            
            # Generate content
            if self.bot_controller and self.bot_controller.content_generator:
                from src.services.enhanced_content_generator import ContentStyle
                
                # Use default style for now
                style = ContentStyle(tone="professional", length="medium")
                
                post = await self.bot_controller.content_generator.generate_post(
                    theme,
                    style,
                    channel_id
                )
                
                # Optimize post
                if self.bot_controller.content_optimizer:
                    post = await self.bot_controller.content_optimizer.optimize(post)
                
                # Store post in context
                context.user_data['generated_post'] = post
                context.user_data['generated_post_id'] = post.id
                
                # Show preview
                await self.show_post_preview(update, context, post)
                
            else:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: сервис генерации контента недоступен",
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при генерации контента\n\n"
                f"<b>Ошибка:</b> {str(e)}\n\n"
                f"Попробуйте позже или выберите другую тему",
                parse_mode='HTML'
            )
    
    async def show_post_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE, post):
        """Show post preview with action buttons.
        
        Args:
            update: Telegram update
            context: Callback context
            post: Generated post object
        """
        logger.info(f"Showing post preview for post {post.id}")
        
        try:
            text = self.formatter.format_post_preview(post)
            keyboard = self.keyboard_builder.build_post_preview_actions(post.id)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Error showing post preview: {e}")
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    f"❌ Ошибка при отображении предпросмотра\n\n{str(e)}",
                    parse_mode='HTML'
                )
    
    async def publish_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
        """Publish post to channel.
        
        Args:
            update: Telegram update
            context: Callback context
            post_id: ID of the post to publish
        """
        logger.info(f"Publishing post {post_id}")
        
        try:
            # Get post from context
            post = context.user_data.get('generated_post')
            
            if not post or post.id != post_id:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: пост не найден\n\n"
                    "Пожалуйста, сгенерируйте пост заново",
                    parse_mode='HTML'
                )
                return
            
            # Show publishing message
            await update.callback_query.edit_message_text(
                "⏳ Публикую пост...",
                parse_mode='HTML'
            )
            
            # Publish post
            if self.bot_controller and self.bot_controller.publishing_service:
                result = await self.bot_controller.publishing_service.publish_post(post)
                
                if result:
                    # Success
                    text = self.formatter.format_success(
                        message="Пост успешно опубликован!",
                        details=f"Пост опубликован в канале"
                    )
                    
                    keyboard = self.keyboard_builder.build_back_button("menu:content")
                    
                    await update.callback_query.edit_message_text(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                    
                    # Clean up context
                    context.user_data.pop('generated_post', None)
                    context.user_data.pop('generated_post_id', None)
                    context.user_data.pop('generation_channel_id', None)
                else:
                    await update.callback_query.edit_message_text(
                        "❌ Не удалось опубликовать пост\n\n"
                        "Проверьте права бота в канале",
                        parse_mode='HTML'
                    )
            else:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: сервис публикации недоступен",
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Error publishing post: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при публикации поста\n\n"
                f"<b>Ошибка:</b> {str(e)}",
                parse_mode='HTML'
            )
    
    async def regenerate_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
        """Regenerate post with same parameters.
        
        Args:
            update: Telegram update
            context: Callback context
            post_id: ID of the post to regenerate
        """
        logger.info(f"Regenerating post {post_id}")
        
        try:
            # Get previous post data
            post = context.user_data.get('generated_post')
            channel_id = context.user_data.get('generation_channel_id')
            
            if not post or not channel_id:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: данные для регенерации не найдены\n\n"
                    "Пожалуйста, начните генерацию заново",
                    parse_mode='HTML'
                )
                return
            
            # Show loading message
            await update.callback_query.edit_message_text(
                "⏳ Генерирую новый вариант поста...",
                parse_mode='HTML'
            )
            
            # Send typing action
            from telegram.constants import ChatAction
            await update.callback_query.message.chat.send_action(ChatAction.TYPING)
            
            # Regenerate with same theme
            theme = post.theme if hasattr(post, 'theme') else "общая тема"
            
            if self.bot_controller and self.bot_controller.content_generator:
                from src.services.enhanced_content_generator import ContentStyle
                
                style = ContentStyle(tone="professional", length="medium")
                
                new_post = await self.bot_controller.content_generator.generate_post(
                    theme,
                    style,
                    channel_id
                )
                
                # Optimize
                if self.bot_controller.content_optimizer:
                    new_post = await self.bot_controller.content_optimizer.optimize(new_post)
                
                # Update context
                context.user_data['generated_post'] = new_post
                context.user_data['generated_post_id'] = new_post.id
                
                # Show new preview
                await self.show_post_preview(update, context, new_post)
            else:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: сервис генерации недоступен",
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Error regenerating post: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при регенерации поста\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def discard_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
        """Discard generated post.
        
        Args:
            update: Telegram update
            context: Callback context
            post_id: ID of the post to discard
        """
        logger.info(f"Discarding post {post_id}")
        
        # Clean up context
        context.user_data.pop('generated_post', None)
        context.user_data.pop('generated_post_id', None)
        context.user_data.pop('generation_channel_id', None)
        
        text = (
            "❌ <b>Пост отменен</b>\n\n"
            "Пост не был опубликован"
        )
        
        keyboard = self.keyboard_builder.build_back_button("menu:content")
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def show_posts_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show list of posts with filtering options.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info(f"Showing posts list to user {update.effective_user.id}")
        
        try:
            # Get channels
            channels = []
            if self.bot_controller and self.bot_controller.channel_manager:
                channels = await self.bot_controller.channel_manager.get_all_channels()
            
            if not channels:
                text = (
                    "📝 <b>Просмотр постов</b>\n\n"
                    "<i>У вас нет зарегистрированных каналов</i>\n\n"
                    "Сначала добавьте канал в разделе <b>Каналы</b>"
                )
                keyboard = self.keyboard_builder.build_back_button("menu:content")
            else:
                text = (
                    "📝 <b>Просмотр постов</b>\n\n"
                    "Выберите канал для просмотра постов:"
                )
                
                # Build channel selection keyboard
                keyboard_buttons = []
                for channel in channels:
                    # Support both dict and object
                    channel_name = channel.get('name') if isinstance(channel, dict) else channel.name
                    channel_id = channel.get('channel_id') if isinstance(channel, dict) else channel.id
                    
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            f"📺 {channel_name}",
                            callback_data=f"posts:channel:{channel_id}"
                        )
                    ])
                
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        "⬅️ Назад",
                        callback_data="menu:content"
                    )
                ])
                
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing posts list: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при загрузке списка постов\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def show_channel_posts(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int, status_filter: str = "all"):
        """Show posts for a specific channel.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
            status_filter: Filter by status (all, draft, scheduled, published)
        """
        logger.info(f"Showing posts for channel {channel_id}, filter: {status_filter}")
        
        try:
            from src.models.base import async_session_maker
            from src.repositories.post_repository import PostRepository
            from src.repositories.channel_repository import ChannelRepository
            from src.models import PostStatus
            
            async with async_session_maker() as session:
                # Get channel
                channel_repo = ChannelRepository(session)
                channel = await channel_repo.get_by_id(channel_id)
                
                if not channel:
                    await update.callback_query.edit_message_text(
                        "❌ Канал не найден",
                        parse_mode='HTML'
                    )
                    return
                
                # Get posts
                post_repo = PostRepository(session)
                
                # Apply status filter
                status = None
                if status_filter == "draft":
                    status = PostStatus.DRAFT
                elif status_filter == "scheduled":
                    status = PostStatus.SCHEDULED
                elif status_filter == "published":
                    status = PostStatus.PUBLISHED
                
                posts = await post_repo.get_by_channel(channel_id, status)
                
                # Build message
                status_emoji = {
                    "all": "📝",
                    "draft": "✏️",
                    "scheduled": "⏰",
                    "published": "✅"
                }
                
                # Support both dict and object
                channel_name = channel.get('name') if isinstance(channel, dict) else channel.name
                
                text = (
                    f"{status_emoji.get(status_filter, '📝')} <b>Посты канала {channel_name}</b>\n\n"
                )
                
                if not posts:
                    text += "<i>Постов не найдено</i>"
                else:
                    text += f"Найдено постов: <b>{len(posts)}</b>\n\n"
                    
                    # Show first 5 posts
                    for i, post in enumerate(posts[:5], 1):
                        status_icon = {
                            PostStatus.DRAFT: "✏️",
                            PostStatus.SCHEDULED: "⏰",
                            PostStatus.PUBLISHED: "✅",
                            PostStatus.FAILED: "❌"
                        }.get(post.status, "📝")
                        
                        # Truncate content
                        content_preview = post.content[:50] + "..." if len(post.content) > 50 else post.content
                        
                        text += f"{i}. {status_icon} {content_preview}\n"
                        if post.scheduled_for:
                            text += f"   📅 {post.scheduled_for.strftime('%d.%m.%Y %H:%M')}\n"
                        text += "\n"
                    
                    if len(posts) > 5:
                        text += f"<i>... и еще {len(posts) - 5} постов</i>\n"
                
                # Build keyboard with filters
                keyboard_buttons = []
                
                # Filter buttons
                filter_row = []
                filters = [
                    ("Все", "all"),
                    ("Черновики", "draft"),
                    ("Запланированные", "scheduled"),
                    ("Опубликованные", "published")
                ]
                
                for label, filter_value in filters:
                    button_text = f"• {label}" if filter_value == status_filter else label
                    filter_row.append(
                        InlineKeyboardButton(
                            button_text,
                            callback_data=f"posts:channel:{channel_id}:{filter_value}"
                        )
                    )
                
                # Split into rows of 2
                keyboard_buttons.append(filter_row[:2])
                keyboard_buttons.append(filter_row[2:])
                
                # Post action buttons (if there are posts)
                if posts:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            "👁️ Просмотреть пост",
                            callback_data=f"posts:view:{posts[0].id}"
                        )
                    ])
                
                # Back button
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        "⬅️ Назад",
                        callback_data="content:view"
                    )
                ])
                
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        
        except Exception as e:
            logger.error(f"Error showing channel posts: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при загрузке постов\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def show_post_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
        """Show detailed view of a specific post.
        
        Args:
            update: Telegram update
            context: Callback context
            post_id: ID of the post
        """
        logger.info(f"Showing post detail for post {post_id}")
        
        try:
            from src.models.base import async_session_maker
            from src.repositories.post_repository import PostRepository
            from src.models import PostStatus
            
            async with async_session_maker() as session:
                post_repo = PostRepository(session)
                post = await post_repo.get_by_id(post_id)
                
                if not post:
                    await update.callback_query.edit_message_text(
                        "❌ Пост не найден",
                        parse_mode='HTML'
                    )
                    return
                
                # Format post details
                status_text = {
                    PostStatus.DRAFT: "✏️ Черновик",
                    PostStatus.SCHEDULED: "⏰ Запланирован",
                    PostStatus.PUBLISHED: "✅ Опубликован",
                    PostStatus.FAILED: "❌ Ошибка публикации"
                }.get(post.status, "📝 Неизвестно")
                
                text = (
                    f"📝 <b>Детали поста</b>\n\n"
                    f"<b>Статус:</b> {status_text}\n"
                )
                
                if post.scheduled_for:
                    text += f"<b>Запланировано на:</b> {post.scheduled_for.strftime('%d.%m.%Y %H:%M')}\n"
                
                if post.published_at:
                    text += f"<b>Опубликовано:</b> {post.published_at.strftime('%d.%m.%Y %H:%M')}\n"
                
                text += f"\n<b>Контент:</b>\n{post.content}\n"
                
                if post.hashtags:
                    text += f"\n<b>Хештеги:</b> {' '.join(post.hashtags)}\n"
                
                # Build action keyboard
                keyboard_buttons = []
                
                # Actions based on status
                if post.status == PostStatus.DRAFT:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            "📤 Опубликовать",
                            callback_data=f"posts:publish:{post_id}"
                        ),
                        InlineKeyboardButton(
                            "⏰ Запланировать",
                            callback_data=f"posts:schedule:{post_id}"
                        )
                    ])
                elif post.status == PostStatus.SCHEDULED:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            "❌ Отменить публикацию",
                            callback_data=f"posts:cancel:{post_id}"
                        )
                    ])
                
                # Common actions
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        "✏️ Редактировать",
                        callback_data=f"posts:edit:{post_id}"
                    ),
                    InlineKeyboardButton(
                        "🗑️ Удалить",
                        callback_data=f"posts:delete:{post_id}"
                    )
                ])
                
                # Back button
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        "⬅️ Назад к списку",
                        callback_data=f"posts:channel:{post.channel_id}"
                    )
                ])
                
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        
        except Exception as e:
            logger.error(f"Error showing post detail: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при загрузке поста\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def _get_channel(self, channel_id: int):
        """Get channel by ID.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Channel object or None
        """
        if not self.bot_controller or not self.bot_controller.channel_manager:
            logger.warning("Channel manager not available")
            return None
        
        try:
            return await self.bot_controller.channel_manager.get_channel_info(channel_id)
        except Exception as e:
            logger.error(f"Error getting channel {channel_id}: {e}")
            return None
