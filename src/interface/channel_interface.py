"""Channel management interface."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from .keyboard_builder import KeyboardBuilder
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class ChannelInterface:
    """Interface for channel management operations."""
    
    def __init__(self, bot_controller=None):
        """Initialize channel interface.
        
        Args:
            bot_controller: Reference to main bot controller
        """
        self.keyboard_builder = KeyboardBuilder()
        self.formatter = MessageFormatter()
        self.bot_controller = bot_controller
    
    async def show_channel_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Show channel dashboard.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Showing dashboard for channel {channel_id}")
        
        try:
            # Get channel info
            channel = await self._get_channel(channel_id)
            
            if not channel:
                await update.callback_query.edit_message_text(
                    "❌ Канал не найден",
                    parse_mode='HTML'
                )
                return
            
            # Get channel statistics
            stats = await self._get_channel_stats(channel_id)
            
            # Format dashboard
            text = self.formatter.format_channel_dashboard(channel, stats)
            keyboard = self.keyboard_builder.build_channel_dashboard(channel)
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing channel dashboard: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка загрузки информации о канале\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def handle_channel_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Handle channel configuration.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Showing config for channel {channel_id}")
        
        try:
            channel = await self._get_channel(channel_id)
            
            if not channel:
                await update.callback_query.edit_message_text(
                    "❌ Канал не найден",
                    parse_mode='HTML'
                )
                return
            
            text = (
                f"⚙️ <b>Настройки канала: {channel.name}</b>\n\n"
                f"🆔 ID: <code>{channel.id}</code>\n"
            )
            
            if hasattr(channel, 'posting_frequency'):
                text += f"📅 Частота: {channel.posting_frequency} постов/день\n"
            
            if hasattr(channel, 'content_style'):
                text += f"🎨 Стиль: {channel.content_style.tone}\n"
            
            text += "\n<i>Настройка параметров будет реализована в следующих версиях</i>"
            
            keyboard = self.keyboard_builder.build_back_button(f"channel:{channel_id}:dashboard")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing channel config: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка загрузки настроек канала",
                parse_mode='HTML'
            )
    
    async def handle_channel_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Handle channel deletion request.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Delete request for channel {channel_id}")
        
        try:
            channel = await self._get_channel(channel_id)
            
            if not channel:
                await update.callback_query.edit_message_text(
                    "❌ Канал не найден",
                    parse_mode='HTML'
                )
                return
            
            # Show confirmation dialog
            text = self.formatter.format_confirmation(
                action="Удаление канала",
                description=f"Вы собираетесь удалить канал <b>{channel.name}</b>",
                consequences=(
                    "• Все настройки канала будут удалены\n"
                    "• История постов будет архивирована\n"
                    "• Запланированные публикации будут отменены\n\n"
                    "<i>Это действие нельзя отменить!</i>"
                )
            )
            
            keyboard = self.keyboard_builder.build_confirmation(
                action="delete_channel",
                data=str(channel_id),
                description=f"Удалить {channel.name}"
            )
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing delete confirmation: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при подготовке удаления канала",
                parse_mode='HTML'
            )
    
    async def confirm_channel_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Confirm and execute channel deletion.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Confirming deletion of channel {channel_id}")
        
        try:
            channel = await self._get_channel(channel_id)
            
            if not channel:
                await update.callback_query.edit_message_text(
                    "❌ Канал не найден",
                    parse_mode='HTML'
                )
                return
            
            channel_name = channel.name
            
            # Delete channel
            if self.bot_controller and self.bot_controller.channel_manager:
                await self.bot_controller.channel_manager.remove_channel(channel_id)
            
            text = self.formatter.format_success(
                message=f"Канал '{channel_name}' успешно удалён",
                details="Все данные канала были архивированы"
            )
            
            keyboard = self.keyboard_builder.build_back_button("menu:channels")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error deleting channel: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при удалении канала\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def cancel_channel_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Cancel channel deletion.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Cancelled deletion of channel {channel_id}")
        
        # Return to channel dashboard
        await self.show_channel_dashboard(update, context, channel_id)
    
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
    
    async def _get_channel_stats(self, channel_id: int) -> dict:
        """Get channel statistics.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Dictionary with statistics
        """
        if not self.bot_controller or not self.bot_controller.analytics:
            return {}
        
        try:
            # Get analytics for the channel
            from datetime import datetime, timedelta
            period_start = datetime.now() - timedelta(days=30)
            
            # This would call analytics engine
            # For now, return mock data
            return {
                'views': 0,
                'engagement_rate': 0.0,
                'posts_count': 0
            }
        except Exception as e:
            logger.error(f"Error getting channel stats: {e}")
            return {}
