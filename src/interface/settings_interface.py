"""Settings interface for bot configuration."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .keyboard_builder import KeyboardBuilder
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class SettingsInterface:
    """Interface for bot settings and configuration."""
    
    def __init__(self, bot_controller=None):
        """Initialize settings interface.
        
        Args:
            bot_controller: Reference to main bot controller
        """
        self.keyboard_builder = KeyboardBuilder()
        self.formatter = MessageFormatter()
        self.bot_controller = bot_controller
    
    async def show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main settings menu with categories.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info("Showing settings menu")
        
        text = (
            "⚙️ <b>Настройки</b>\n\n"
            "Выберите категорию настроек:"
        )
        
        keyboard_buttons = [
            [InlineKeyboardButton("📅 Частота публикаций", callback_data="settings:frequency")],
            [InlineKeyboardButton("✍️ Стиль контента", callback_data="settings:style")],
            [InlineKeyboardButton("🔔 Уведомления", callback_data="settings:notifications")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="menu:main")]
        ]
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def show_frequency_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show posting frequency settings.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info("Showing frequency settings")
        
        # Get current frequency
        current_frequency = await self._get_setting('posting_frequency', 3)
        
        text = (
            "📅 <b>Частота публикаций</b>\n\n"
            f"Текущая частота: <b>{current_frequency} постов/день</b>\n\n"
            "Выберите новую частоту:"
        )
        
        # Preset options
        keyboard_buttons = [
            [
                InlineKeyboardButton("1 пост", callback_data="settings:frequency:1"),
                InlineKeyboardButton("2 поста", callback_data="settings:frequency:2"),
                InlineKeyboardButton("3 поста", callback_data="settings:frequency:3")
            ],
            [
                InlineKeyboardButton("5 постов", callback_data="settings:frequency:5"),
                InlineKeyboardButton("10 постов", callback_data="settings:frequency:10"),
                InlineKeyboardButton("24 поста", callback_data="settings:frequency:24")
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu:settings")]
        ]
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def update_frequency(self, update: Update, context: ContextTypes.DEFAULT_TYPE, frequency: int):
        """Update posting frequency setting.
        
        Args:
            update: Telegram update
            context: Callback context
            frequency: New frequency value (1-24)
        """
        logger.info(f"Updating frequency to {frequency}")
        
        try:
            # Validate frequency
            if not 1 <= frequency <= 24:
                await update.callback_query.edit_message_text(
                    "❌ <b>Ошибка валидации</b>\n\n"
                    "Частота должна быть от 1 до 24 постов в день.\n\n"
                    "Попробуйте снова.",
                    parse_mode='HTML'
                )
                return
            
            # Save setting
            await self._save_setting('posting_frequency', frequency)
            
            # Show confirmation
            text = (
                "✅ <b>Настройка обновлена</b>\n\n"
                f"Частота публикаций: <b>{frequency} постов/день</b>\n\n"
                "Изменения вступят в силу для новых публикаций."
            )
            
            keyboard = self.keyboard_builder.build_back_button("menu:settings")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error updating frequency: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка сохранения настройки\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def show_style_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show content style settings.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info("Showing style settings")
        
        # Get current style
        current_style = await self._get_setting('content_style', 'professional')
        
        style_names = {
            'professional': 'Профессиональный',
            'casual': 'Неформальный',
            'humorous': 'Юмористический'
        }
        
        text = (
            "✍️ <b>Стиль контента</b>\n\n"
            f"Текущий стиль: <b>{style_names.get(current_style, current_style)}</b>\n\n"
            "Выберите новый стиль:"
        )
        
        keyboard_buttons = [
            [InlineKeyboardButton(
                "👔 Профессиональный",
                callback_data="settings:style:professional"
            )],
            [InlineKeyboardButton(
                "😊 Неформальный",
                callback_data="settings:style:casual"
            )],
            [InlineKeyboardButton(
                "😄 Юмористический",
                callback_data="settings:style:humorous"
            )],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu:settings")]
        ]
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def update_style(self, update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
        """Update content style setting.
        
        Args:
            update: Telegram update
            context: Callback context
            style: New style value
        """
        logger.info(f"Updating style to {style}")
        
        try:
            # Validate style
            valid_styles = ['professional', 'casual', 'humorous']
            if style not in valid_styles:
                await update.callback_query.edit_message_text(
                    "❌ <b>Ошибка валидации</b>\n\n"
                    "Неверный стиль контента.\n\n"
                    "Попробуйте снова.",
                    parse_mode='HTML'
                )
                return
            
            # Save setting
            await self._save_setting('content_style', style)
            
            style_names = {
                'professional': 'Профессиональный',
                'casual': 'Неформальный',
                'humorous': 'Юмористический'
            }
            
            # Show confirmation
            text = (
                "✅ <b>Настройка обновлена</b>\n\n"
                f"Стиль контента: <b>{style_names[style]}</b>\n\n"
                "Изменения вступят в силу для нового контента."
            )
            
            keyboard = self.keyboard_builder.build_back_button("menu:settings")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error updating style: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка сохранения настройки\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def show_notification_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show notification settings.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info("Showing notification settings")
        
        # Get current notification settings
        notify_success = await self._get_setting('notify_success', True)
        notify_errors = await self._get_setting('notify_errors', True)
        notify_analytics = await self._get_setting('notify_analytics', False)
        
        text = (
            "🔔 <b>Уведомления</b>\n\n"
            "Настройте, какие уведомления вы хотите получать:\n\n"
            f"{'✅' if notify_success else '❌'} Успешные публикации\n"
            f"{'✅' if notify_errors else '❌'} Ошибки и проблемы\n"
            f"{'✅' if notify_analytics else '❌'} Еженедельная аналитика"
        )
        
        keyboard_buttons = [
            [InlineKeyboardButton(
                f"{'✅' if notify_success else '❌'} Успешные публикации",
                callback_data=f"settings:notify:success:{not notify_success}"
            )],
            [InlineKeyboardButton(
                f"{'✅' if notify_errors else '❌'} Ошибки и проблемы",
                callback_data=f"settings:notify:errors:{not notify_errors}"
            )],
            [InlineKeyboardButton(
                f"{'✅' if notify_analytics else '❌'} Еженедельная аналитика",
                callback_data=f"settings:notify:analytics:{not notify_analytics}"
            )],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu:settings")]
        ]
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def toggle_notification(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  notification_type: str, enabled: bool):
        """Toggle notification setting.
        
        Args:
            update: Telegram update
            context: Callback context
            notification_type: Type of notification (success, errors, analytics)
            enabled: New enabled state
        """
        logger.info(f"Toggling notification {notification_type} to {enabled}")
        
        try:
            # Save setting
            setting_key = f'notify_{notification_type}'
            await self._save_setting(setting_key, enabled)
            
            # Refresh the menu to show updated state
            await self.show_notification_settings(update, context)
            
        except Exception as e:
            logger.error(f"Error toggling notification: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка сохранения настройки\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def _get_setting(self, key: str, default=None):
        """Get setting value.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value
        """
        # Use bot controller's settings storage if available
        if self.bot_controller and hasattr(self.bot_controller, 'settings_storage'):
            try:
                return await self.bot_controller.settings_storage.get(key, default)
            except Exception as e:
                logger.error(f"Error getting setting {key}: {e}")
        
        # Fallback to default
        return default
    
    async def _save_setting(self, key: str, value):
        """Save setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        logger.info(f"Saving setting {key}={value}")
        
        # Use bot controller's settings storage if available
        if self.bot_controller and hasattr(self.bot_controller, 'settings_storage'):
            try:
                await self.bot_controller.settings_storage.set(key, value)
                logger.info(f"Setting {key} saved successfully")
            except Exception as e:
                logger.error(f"Error saving setting {key}: {e}")
                raise
        else:
            logger.warning(f"Settings storage not available, setting {key} not persisted")
