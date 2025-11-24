"""Schedule interface for managing scheduled posts."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from .keyboard_builder import KeyboardBuilder
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class ScheduleInterface:
    """Interface for scheduling posts."""
    
    def __init__(self, bot_controller=None):
        """Initialize schedule interface.
        
        Args:
            bot_controller: Reference to main bot controller
        """
        self.keyboard_builder = KeyboardBuilder()
        self.formatter = MessageFormatter()
        self.bot_controller = bot_controller
    
    async def show_schedule_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show schedule menu with upcoming posts.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info("Showing schedule menu")
        
        try:
            # Get scheduled posts
            scheduled_posts = await self._get_scheduled_posts()
            
            if not scheduled_posts:
                text = (
                    "📅 <b>Расписание публикаций</b>\n\n"
                    "📭 <b>Нет запланированных постов</b>\n\n"
                    "Запланируйте публикацию, чтобы автоматизировать контент."
                )
                
                keyboard_buttons = [
                    [InlineKeyboardButton("➕ Запланировать пост", callback_data="schedule:create")],
                    [InlineKeyboardButton("⬅️ Главное меню", callback_data="menu:main")]
                ]
            else:
                text = (
                    "📅 <b>Расписание публикаций</b>\n\n"
                    f"Запланировано постов: <b>{len(scheduled_posts)}</b>\n\n"
                )
                
                # Show upcoming posts
                for i, post in enumerate(scheduled_posts[:5], 1):
                    channel_name = post.get('channel_name', 'Неизвестный канал')
                    scheduled_time = post.get('scheduled_time')
                    theme = post.get('theme', 'Без темы')
                    
                    time_str = scheduled_time.strftime('%d.%m.%Y %H:%M') if scheduled_time else 'Не указано'
                    text += f"{i}. 📺 {channel_name}\n"
                    text += f"   ⏰ {time_str}\n"
                    text += f"   📝 {theme}\n\n"
                
                keyboard_buttons = [
                    [InlineKeyboardButton("➕ Запланировать пост", callback_data="schedule:create")],
                    [InlineKeyboardButton("⬅️ Главное меню", callback_data="menu:main")]
                ]
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing schedule menu: {e}")
            text = (
                "❌ <b>Ошибка загрузки расписания</b>\n\n"
                f"Не удалось загрузить запланированные посты.\n\n"
                f"<i>Ошибка: {str(e)}</i>"
            )
            keyboard = self.keyboard_builder.build_back_button("menu:main")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    async def start_schedule_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start schedule creation flow - channel selection.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info("Starting schedule creation")
        
        try:
            # Get all channels
            channels = await self._get_all_channels()
            
            if not channels:
                text = (
                    "❌ <b>Нет каналов</b>\n\n"
                    "Добавьте канал, чтобы планировать публикации.\n\n"
                    "💡 Используйте меню <b>Каналы</b> → <b>Добавить канал</b>"
                )
                keyboard = self.keyboard_builder.build_back_button("menu:main")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return
            
            # Show channel selection
            text = (
                "📅 <b>Планирование публикации</b>\n\n"
                "Шаг 1/3: Выберите канал для публикации:"
            )
            
            keyboard_buttons = []
            for channel in channels:
                button_text = f"📺 {channel.name}"
                callback_data = f"schedule:channel:{channel.id}"
                keyboard_buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            keyboard_buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="menu:main")])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error starting schedule creation: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                parse_mode='HTML'
            )
    
    async def show_time_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Show time selection for scheduling.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: Selected channel ID
        """
        logger.info(f"Showing time selection for channel {channel_id}")
        
        # Store channel in context
        context.user_data['schedule_channel_id'] = channel_id
        
        text = (
            "📅 <b>Планирование публикации</b>\n\n"
            "Шаг 2/3: Выберите время публикации:"
        )
        
        # Generate time options
        now = datetime.now()
        keyboard_buttons = []
        
        # Today options
        today_buttons = []
        for hour in [12, 15, 18, 21]:
            scheduled_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if scheduled_time > now:
                time_str = scheduled_time.strftime('%H:%M')
                callback_data = f"schedule:time:{scheduled_time.timestamp()}"
                today_buttons.append(InlineKeyboardButton(f"Сегодня {time_str}", callback_data=callback_data))
        
        if today_buttons:
            keyboard_buttons.extend([[btn] for btn in today_buttons])
        
        # Tomorrow options
        tomorrow = now + timedelta(days=1)
        tomorrow_buttons = []
        for hour in [9, 12, 15, 18]:
            scheduled_time = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
            time_str = scheduled_time.strftime('%H:%M')
            callback_data = f"schedule:time:{scheduled_time.timestamp()}"
            tomorrow_buttons.append(InlineKeyboardButton(f"Завтра {time_str}", callback_data=callback_data))
        
        keyboard_buttons.extend([[btn] for btn in tomorrow_buttons])
        
        keyboard_buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="menu:main")])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def show_theme_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, scheduled_time: float):
        """Show theme selection for scheduled post.
        
        Args:
            update: Telegram update
            context: Callback context
            scheduled_time: Scheduled time as timestamp
        """
        logger.info(f"Showing theme selection for time {scheduled_time}")
        
        # Store time in context
        context.user_data['schedule_time'] = scheduled_time
        
        scheduled_dt = datetime.fromtimestamp(scheduled_time)
        time_str = scheduled_dt.strftime('%d.%m.%Y %H:%M')
        
        text = (
            "📅 <b>Планирование публикации</b>\n\n"
            f"Время: <b>{time_str}</b>\n\n"
            "Шаг 3/3: Выберите тему контента:"
        )
        
        # Preset themes
        keyboard_buttons = [
            [InlineKeyboardButton("💻 Технологии", callback_data="schedule:theme:tech")],
            [InlineKeyboardButton("🎨 Дизайн", callback_data="schedule:theme:design")],
            [InlineKeyboardButton("📱 Мобильные приложения", callback_data="schedule:theme:mobile")],
            [InlineKeyboardButton("🚀 Стартапы", callback_data="schedule:theme:startup")],
            [InlineKeyboardButton("✏️ Своя тема", callback_data="schedule:theme:custom")],
            [InlineKeyboardButton("❌ Отмена", callback_data="menu:main")]
        ]
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def create_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE, theme: str):
        """Create scheduled post.
        
        Args:
            update: Telegram update
            context: Callback context
            theme: Selected theme
        """
        logger.info(f"Creating schedule with theme {theme}")
        
        try:
            # Get data from context
            channel_id = context.user_data.get('schedule_channel_id')
            scheduled_time = context.user_data.get('schedule_time')
            
            if not channel_id or not scheduled_time:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: данные планирования потеряны. Попробуйте снова.",
                    parse_mode='HTML'
                )
                return
            
            # Map theme codes to readable names
            theme_names = {
                'tech': 'Технологии',
                'design': 'Дизайн',
                'mobile': 'Мобильные приложения',
                'startup': 'Стартапы',
                'custom': 'Пользовательская тема'
            }
            
            theme_name = theme_names.get(theme, theme)
            
            # Get channel info
            channel = await self._get_channel(channel_id)
            if not channel:
                await update.callback_query.edit_message_text(
                    "❌ Канал не найден",
                    parse_mode='HTML'
                )
                return
            
            # Show loading
            await update.callback_query.edit_message_text(
                "⏳ Создаю расписание...",
                parse_mode='HTML'
            )
            
            # Create schedule
            scheduled_dt = datetime.fromtimestamp(scheduled_time)
            success = await self._create_schedule(channel_id, scheduled_dt, theme_name)
            
            if success:
                time_str = scheduled_dt.strftime('%d.%m.%Y %H:%M')
                
                text = (
                    "✅ <b>Публикация запланирована</b>\n\n"
                    f"📺 Канал: <b>{channel.name}</b>\n"
                    f"⏰ Время: <b>{time_str}</b>\n"
                    f"📝 Тема: <b>{theme_name}</b>\n\n"
                    "Пост будет автоматически сгенерирован и опубликован в указанное время."
                )
                
                keyboard = self.keyboard_builder.build_back_button("menu:main")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                await update.callback_query.edit_message_text(
                    "❌ Не удалось создать расписание. Попробуйте позже.",
                    parse_mode='HTML'
                )
            
            # Clear context
            context.user_data.pop('schedule_channel_id', None)
            context.user_data.pop('schedule_time', None)
            
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка создания расписания\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def cancel_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE, schedule_id: int):
        """Cancel scheduled post.
        
        Args:
            update: Telegram update
            context: Callback context
            schedule_id: ID of schedule to cancel
        """
        logger.info(f"Canceling schedule {schedule_id}")
        
        try:
            success = await self._cancel_schedule(schedule_id)
            
            if success:
                await update.callback_query.edit_message_text(
                    "✅ Запланированная публикация отменена",
                    parse_mode='HTML'
                )
            else:
                await update.callback_query.edit_message_text(
                    "❌ Не удалось отменить публикацию",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error canceling schedule: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка отмены: {str(e)}",
                parse_mode='HTML'
            )
    
    async def _get_all_channels(self):
        """Get all registered channels.
        
        Returns:
            List of channel objects
        """
        if not self.bot_controller or not self.bot_controller.channel_manager:
            logger.warning("Channel manager not available")
            return []
        
        try:
            return await self.bot_controller.channel_manager.get_all_channels()
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
            return []
    
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
    
    async def _get_scheduled_posts(self):
        """Get all scheduled posts.
        
        Returns:
            List of scheduled posts
        """
        if not self.bot_controller or not self.bot_controller.scheduler:
            logger.warning("Scheduler not available")
            return []
        
        try:
            return await self.bot_controller.scheduler.get_scheduled_posts()
        except Exception as e:
            logger.error(f"Error getting scheduled posts: {e}")
            return []
    
    async def _create_schedule(self, channel_id: int, scheduled_time: datetime, theme: str) -> bool:
        """Create a new schedule.
        
        Args:
            channel_id: Channel ID
            scheduled_time: When to publish
            theme: Content theme
            
        Returns:
            True if successful
        """
        if not self.bot_controller or not self.bot_controller.scheduler:
            logger.warning("Scheduler not available")
            return False
        
        try:
            await self.bot_controller.scheduler.schedule_post(
                channel_id=channel_id,
                scheduled_time=scheduled_time,
                theme=theme
            )
            return True
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return False
    
    async def _cancel_schedule(self, schedule_id: int) -> bool:
        """Cancel a schedule.
        
        Args:
            schedule_id: Schedule ID to cancel
            
        Returns:
            True if successful
        """
        if not self.bot_controller or not self.bot_controller.scheduler:
            logger.warning("Scheduler not available")
            return False
        
        try:
            await self.bot_controller.scheduler.cancel_schedule(schedule_id)
            return True
        except Exception as e:
            logger.error(f"Error canceling schedule: {e}")
            return False
