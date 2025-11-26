"""Analytics interface for viewing channel statistics."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from .keyboard_builder import KeyboardBuilder
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class AnalyticsInterface:
    """Interface for analytics and statistics."""
    
    def __init__(self, bot_controller=None):
        """Initialize analytics interface.
        
        Args:
            bot_controller: Reference to main bot controller
        """
        self.keyboard_builder = KeyboardBuilder()
        self.formatter = MessageFormatter()
        self.bot_controller = bot_controller
    
    async def show_analytics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show analytics menu with channel selection.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info("Showing analytics menu")
        
        try:
            # Get all channels
            channels = await self._get_all_channels()
            
            if not channels:
                text = (
                    "📊 <b>Аналитика</b>\n\n"
                    "❌ <b>Нет каналов</b>\n\n"
                    "Добавьте канал, чтобы просматривать аналитику.\n\n"
                    "💡 Используйте меню <b>Каналы</b> → <b>Добавить канал</b>"
                )
                keyboard = self.keyboard_builder.build_back_button("menu:main")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return
            
            # Build channel selection menu
            text = (
                "📊 <b>Аналитика</b>\n\n"
                "Выберите канал для просмотра статистики:"
            )
            
            keyboard_buttons = []
            for channel in channels:
                # Support both dict and object
                channel_name = channel.get('name') if isinstance(channel, dict) else channel.name
                channel_id = channel.get('channel_id') if isinstance(channel, dict) else channel.id
                
                button_text = f"📈 {channel_name}"
                callback_data = f"analytics:{channel_id}"
                keyboard_buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Add back button
            keyboard_buttons.append([InlineKeyboardButton("⬅️ Главное меню", callback_data="menu:main")])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing analytics menu: {e}")
            text = (
                "❌ <b>Ошибка загрузки меню</b>\n\n"
                f"Не удалось загрузить список каналов.\n\n"
                f"<i>Ошибка: {str(e)}</i>"
            )
            keyboard = self.keyboard_builder.build_back_button("menu:main")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    async def show_channel_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Show analytics for specific channel.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Showing analytics for channel {channel_id}")
        
        try:
            # Get channel info
            channel = await self._get_channel(channel_id)
            
            if not channel:
                text = (
                    "❌ <b>Канал не найден</b>\n\n"
                    "Канал может быть удален или недоступен"
                )
                keyboard = self.keyboard_builder.build_back_button("menu:analytics")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return
            
            # Get analytics data
            metrics = await self._get_channel_metrics(channel_id)
            
            # Support both dict and object
            channel_name = channel.get('name') if isinstance(channel, dict) else channel.name
            
            if not metrics or metrics.get('no_data'):
                # No data available
                text = (
                    f"📈 <b>Аналитика: {channel_name}</b>\n\n"
                    f"📊 <b>Данные недоступны</b>\n\n"
                    f"<i>Возможные причины:</i>\n"
                    f"• Канал недавно добавлен\n"
                    f"• Нет опубликованных постов\n"
                    f"• Статистика еще не собрана\n\n"
                    f"💡 <b>Что делать:</b>\n"
                    f"• Опубликуйте несколько постов\n"
                    f"• Подождите 24 часа\n"
                    f"• Проверьте аналитику снова"
                )
                
                keyboard = self.keyboard_builder.build_back_button("menu:analytics")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return
            
            # Format analytics
            text = self.formatter.format_analytics(channel_name, metrics)
            
            # Build keyboard with actions
            keyboard_buttons = [
                [InlineKeyboardButton("📄 Детальный отчет", callback_data=f"analytics:{channel_id}:detailed")],
                [InlineKeyboardButton("🔄 Обновить", callback_data=f"analytics:{channel_id}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="menu:analytics")]
            ]
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            try:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                # If message is not modified, just answer the callback
                if "message is not modified" in str(e).lower():
                    await update.callback_query.answer("Данные уже актуальны")
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Error showing analytics: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка загрузки аналитики\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def show_detailed_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Show detailed analytics report.
        
        Args:
            update: Telegram update
            context: Callback context
            channel_id: ID of the channel
        """
        logger.info(f"Generating detailed report for channel {channel_id}")
        
        try:
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
                "⏳ Генерирую детальный отчет...",
                parse_mode='HTML'
            )
            
            # Get detailed metrics
            metrics = await self._get_channel_metrics(channel_id, detailed=True)
            
            if not metrics or metrics.get('no_data'):
                await update.callback_query.edit_message_text(
                    "❌ Недостаточно данных для детального отчета",
                    parse_mode='HTML'
                )
                return
            
            # Support both dict and object
            channel_name = channel.get('name') if isinstance(channel, dict) else channel.name
            
            # Format detailed report
            text = self._format_detailed_report(channel_name, metrics)
            
            keyboard = self.keyboard_builder.build_back_button(f"analytics:{channel_id}")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error generating detailed report: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка генерации отчета\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    def _format_detailed_report(self, channel_name: str, metrics: dict) -> str:
        """Format detailed analytics report.
        
        Args:
            channel_name: Name of the channel
            metrics: Detailed metrics dictionary
            
        Returns:
            Formatted report text
        """
        text = f"📊 <b>Детальный отчет: {channel_name}</b>\n\n"
        
        # Period
        period = metrics.get('period', 'последние 30 дней')
        text += f"📅 <b>Период:</b> {period}\n\n"
        
        # Overview
        text += "📈 <b>Общая статистика:</b>\n"
        text += f"👁️ Просмотры: {metrics.get('views', 0):,}\n"
        text += f"❤️ Реакции: {metrics.get('reactions', 0):,}\n"
        text += f"📤 Репосты: {metrics.get('shares', 0):,}\n"
        text += f"💬 Комментарии: {metrics.get('comments', 0):,}\n"
        text += f"📊 Вовлеченность: {metrics.get('engagement_rate', 0):.2f}%\n"
        text += f"📝 Всего постов: {metrics.get('total_posts', 0)}\n\n"
        
        # Growth
        if 'growth' in metrics:
            growth = metrics['growth']
            growth_emoji = "📈" if growth >= 0 else "📉"
            text += f"{growth_emoji} <b>Рост:</b> {growth:+.1f}%\n\n"
        
        # Top posts
        if 'top_posts' in metrics and metrics['top_posts']:
            text += "🔥 <b>Топ-5 постов:</b>\n"
            for i, post in enumerate(metrics['top_posts'][:5], 1):
                views = post.get('views', 0)
                engagement = post.get('engagement_rate', 0)
                text += f"{i}. {views:,} 👁️ | {engagement:.1f}% 📊\n"
            text += "\n"
        
        # Best time to post
        if 'best_time' in metrics:
            text += f"⏰ <b>Лучшее время:</b> {metrics['best_time']}\n\n"
        
        # Recommendations
        if 'recommendations' in metrics:
            text += "💡 <b>Рекомендации:</b>\n"
            for rec in metrics['recommendations'][:3]:
                text += f"• {rec}\n"
        
        return text
    
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
    
    async def _get_channel_metrics(self, channel_id: int, detailed: bool = False) -> dict:
        """Get channel metrics.
        
        Args:
            channel_id: ID of the channel
            detailed: Whether to get detailed metrics
            
        Returns:
            Dictionary with metrics
        """
        if not self.bot_controller or not self.bot_controller.analytics:
            logger.warning("Analytics engine not available")
            return {'no_data': True}
        
        try:
            # Get analytics from engine
            period_start = datetime.now() - timedelta(days=30)
            period_end = datetime.now()
            
            # Call analytics engine
            metrics = await self.bot_controller.analytics.get_channel_analytics(
                channel_id,
                period_start,
                period_end
            )
            
            if not metrics or not metrics.get('views'):
                return {'no_data': True}
            
            # Add period info
            metrics['period'] = 'последние 30 дней'
            
            # Add recommendations if detailed
            if detailed:
                metrics['recommendations'] = [
                    "Публикуйте в 18:00-20:00 для максимального охвата",
                    "Используйте больше визуального контента",
                    "Добавляйте вопросы для повышения вовлеченности"
                ]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for channel {channel_id}: {e}")
            return {'no_data': True}
