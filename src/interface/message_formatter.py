"""Message formatter for consistent message styling."""

from datetime import datetime
from typing import Optional


class MessageFormatter:
    """Formatter for creating styled messages with emojis."""
    
    @staticmethod
    def format_main_menu() -> str:
        """Format main menu message.
        
        Returns:
            Formatted main menu text
        """
        return (
            "🤖 <b>AI Content Bot</b>\n\n"
            "Выберите раздел для управления:\n\n"
            "📊 <b>Каналы</b> - управление каналами\n"
            "✍️ <b>Контент</b> - создание и планирование\n"
            "📈 <b>Аналитика</b> - статистика и отчёты\n"
            "⚙️ <b>Настройки</b> - конфигурация бота\n\n"
            "⚡ <b>Быстрые действия:</b>\n"
            "• Сгенерировать пост прямо сейчас\n"
            "• Посмотреть статус системы"
        )
    
    @staticmethod
    def format_channel_info(channel) -> str:
        """Format channel information.
        
        Args:
            channel: Channel object or dict
            
        Returns:
            Formatted channel info text
        """
        # Support both dict and object
        if isinstance(channel, dict):
            active = channel.get('active', True)
            name = channel.get('name') or channel.get('title', 'Без названия')
            channel_id = channel.get('id')
            posting_frequency = channel.get('posting_frequency')
            themes = channel.get('themes')
        else:
            active = channel.active
            name = channel.name
            channel_id = channel.id
            posting_frequency = getattr(channel, 'posting_frequency', None)
            themes = getattr(channel, 'themes', None)
        
        status_emoji = "✅" if active else "⏸️"
        
        text = (
            f"📺 <b>{name}</b>\n\n"
            f"🆔 ID: <code>{channel_id}</code>\n"
            f"📊 Статус: {status_emoji} {'Активен' if active else 'Приостановлен'}\n"
        )
        
        if posting_frequency:
            text += f"📅 Частота: {posting_frequency} постов/день\n"
        
        if themes:
            themes_str = ", ".join(themes[:3])
            text += f"🎯 Темы: {themes_str}\n"
        
        return text
    
    @staticmethod
    def format_channel_dashboard(channel, stats: Optional[dict] = None) -> str:
        """Format channel dashboard.
        
        Args:
            channel: Channel object
            stats: Optional statistics dictionary
            
        Returns:
            Formatted dashboard text
        """
        text = MessageFormatter.format_channel_info(channel)
        
        if stats:
            text += "\n📈 <b>Статистика:</b>\n"
            text += f"👁️ Просмотры: {stats.get('views', 0):,}\n"
            text += f"❤️ Вовлеченность: {stats.get('engagement_rate', 0):.1f}%\n"
            text += f"📝 Постов: {stats.get('posts_count', 0)}\n"
        
        text += "\n<i>Выберите действие:</i>"
        
        return text
    
    @staticmethod
    def format_post_preview(post) -> str:
        """Format post preview.
        
        Args:
            post: Post object
            
        Returns:
            Formatted post preview text
        """
        text = "📝 <b>Предпросмотр поста:</b>\n\n"
        text += "─" * 30 + "\n\n"
        text += post.content + "\n\n"
        
        if post.hashtags:
            text += " ".join(post.hashtags) + "\n\n"
        
        text += "─" * 30 + "\n\n"
        text += "<i>Выберите действие с постом:</i>"
        
        return text
    
    @staticmethod
    def format_analytics(channel_name: str, metrics: dict) -> str:
        """Format analytics data.
        
        Args:
            channel_name: Name of the channel
            metrics: Dictionary with metrics
            
        Returns:
            Formatted analytics text
        """
        text = f"📊 <b>Аналитика: {channel_name}</b>\n\n"
        
        # Overview metrics
        text += "📈 <b>Обзор:</b>\n"
        text += f"👁️ Просмотры: {metrics.get('views', 0):,}\n"
        text += f"❤️ Реакции: {metrics.get('reactions', 0):,}\n"
        text += f"📤 Репосты: {metrics.get('shares', 0):,}\n"
        text += f"💬 Комментарии: {metrics.get('comments', 0):,}\n"
        text += f"📊 Вовлеченность: {metrics.get('engagement_rate', 0):.2f}%\n\n"
        
        # Top posts
        if 'top_posts' in metrics and metrics['top_posts']:
            text += "🔥 <b>Топ постов:</b>\n"
            for i, post in enumerate(metrics['top_posts'][:3], 1):
                text += f"{i}. {post.get('title', 'Пост')} - {post.get('views', 0):,} 👁️\n"
            text += "\n"
        
        # Period
        if 'period' in metrics:
            text += f"📅 Период: {metrics['period']}\n"
        
        return text
    
    @staticmethod
    def format_error(error: str, suggestion: str = "") -> str:
        """Format error message.
        
        Args:
            error: Error description
            suggestion: Optional suggestion for fixing
            
        Returns:
            Formatted error message
        """
        text = f"❌ <b>Ошибка:</b> {error}\n"
        
        if suggestion:
            text += f"\n💡 <b>Совет:</b> {suggestion}"
        
        return text
    
    @staticmethod
    def format_success(message: str, details: str = "") -> str:
        """Format success message.
        
        Args:
            message: Success message
            details: Optional details
            
        Returns:
            Formatted success message
        """
        text = f"✅ <b>Успешно:</b> {message}\n"
        
        if details:
            text += f"\n{details}"
        
        return text
    
    @staticmethod
    def format_confirmation(action: str, description: str, consequences: str = "") -> str:
        """Format confirmation dialog.
        
        Args:
            action: Action to confirm
            description: Description of the action
            consequences: Optional consequences description
            
        Returns:
            Formatted confirmation text
        """
        text = f"⚠️ <b>Подтверждение действия</b>\n\n"
        text += f"<b>Действие:</b> {action}\n"
        text += f"<b>Описание:</b> {description}\n"
        
        if consequences:
            text += f"\n<b>⚠️ Последствия:</b>\n{consequences}\n"
        
        text += "\n<i>Вы уверены?</i>"
        
        return text
    
    @staticmethod
    def format_system_status(resources: dict, bot_status: str) -> str:
        """Format system status.
        
        Args:
            resources: Dictionary with resource usage
            bot_status: Bot status string
            
        Returns:
            Formatted status text
        """
        text = "📊 <b>Статус системы</b>\n\n"
        
        # Bot status
        status_emoji = "✅" if bot_status == "running" else "⏸️"
        text += f"🤖 Бот: {status_emoji} {bot_status}\n\n"
        
        # Resources
        text += "💻 <b>Ресурсы:</b>\n"
        
        cpu = resources.get('cpu_percent', 0)
        cpu_emoji = "🟢" if cpu < 50 else "🟡" if cpu < 80 else "🔴"
        text += f"{cpu_emoji} CPU: {cpu:.1f}%\n"
        
        memory = resources.get('memory_percent', 0)
        mem_emoji = "🟢" if memory < 50 else "🟡" if memory < 80 else "🔴"
        text += f"{mem_emoji} Память: {memory:.1f}%\n"
        
        disk = resources.get('disk_percent', 0)
        disk_emoji = "🟢" if disk < 70 else "🟡" if disk < 90 else "🔴"
        text += f"{disk_emoji} Диск: {disk:.1f}%\n"
        
        # Errors
        if 'error_count' in resources:
            text += f"\n📝 Ошибок за сессию: {resources['error_count']}\n"
        
        # Uptime
        if 'uptime' in resources:
            text += f"⏱️ Время работы: {resources['uptime']}\n"
        
        return text
    
    @staticmethod
    def format_help(context: str, content: str) -> str:
        """Format help message.
        
        Args:
            context: Help context
            content: Help content
            
        Returns:
            Formatted help text
        """
        text = f"❓ <b>Помощь: {context}</b>\n\n"
        text += content
        
        return text
    
    @staticmethod
    def format_loading(message: str = "Обработка...") -> str:
        """Format loading message.
        
        Args:
            message: Loading message
            
        Returns:
            Formatted loading text
        """
        return f"⏳ {message}"
    
    @staticmethod
    def format_scheduled_posts(posts: list) -> str:
        """Format scheduled posts list.
        
        Args:
            posts: List of scheduled post objects
            
        Returns:
            Formatted scheduled posts text
        """
        if not posts:
            return "📅 <b>Запланированные посты</b>\n\n<i>Нет запланированных постов</i>"
        
        text = "📅 <b>Запланированные посты</b>\n\n"
        
        for post in posts:
            scheduled_time = post.scheduled_time.strftime("%d.%m.%Y %H:%M")
            text += f"🕐 {scheduled_time}\n"
            text += f"📺 {post.channel_name}\n"
            
            # Preview
            preview = post.content[:50] + "..." if len(post.content) > 50 else post.content
            text += f"📝 {preview}\n"
            text += "─" * 20 + "\n\n"
        
        return text
    
    @staticmethod
    def format_notification_settings(settings: dict) -> str:
        """Format notification settings.
        
        Args:
            settings: Dictionary with notification settings
            
        Returns:
            Formatted settings text
        """
        text = "🔔 <b>Настройки уведомлений</b>\n\n"
        
        for category, enabled in settings.items():
            emoji = "✅" if enabled else "❌"
            category_name = {
                'errors': 'Ошибки',
                'completions': 'Завершения',
                'milestones': 'Важные события',
                'analytics': 'Аналитика'
            }.get(category, category)
            
            text += f"{emoji} {category_name}\n"
        
        text += "\n<i>Нажмите на категорию для переключения</i>"
        
        return text
