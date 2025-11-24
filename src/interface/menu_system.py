"""Menu system for bot interface."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from .keyboard_builder import KeyboardBuilder
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class MenuSystem:
    """Manages menu navigation and display."""
    
    def __init__(self, bot_controller=None):
        """Initialize menu system.
        
        Args:
            bot_controller: Reference to main bot controller
        """
        self.keyboard_builder = KeyboardBuilder()
        self.formatter = MessageFormatter()
        self.bot_controller = bot_controller
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info(f"Showing main menu to user {update.effective_user.id}")
        
        # Store current menu in context
        context.user_data['current_menu'] = 'main'
        context.user_data['previous_menu'] = context.user_data.get('current_menu')
        
        # Build menu
        text = self.formatter.format_main_menu()
        keyboard = self.keyboard_builder.build_main_menu()
        
        # Send or edit message
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
    
    async def show_channels_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show channels menu.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info(f"Showing channels menu to user {update.effective_user.id}")
        
        # Store navigation
        context.user_data['previous_menu'] = context.user_data.get('current_menu', 'main')
        context.user_data['current_menu'] = 'channels'
        
        # Get channels from bot controller
        channels = []
        if self.bot_controller and self.bot_controller.channel_manager:
            try:
                channels = await self.bot_controller.channel_manager.get_all_channels()
            except Exception as e:
                logger.error(f"Failed to get channels: {e}")
        
        # Get page number
        page = context.user_data.get('channels_page', 0)
        
        # Build menu
        if not channels:
            text = (
                "📊 <b>Управление каналами</b>\n\n"
                "<i>У вас пока нет зарегистрированных каналов</i>\n\n"
                "Нажмите <b>Добавить канал</b> для регистрации первого канала"
            )
        else:
            text = (
                f"📊 <b>Управление каналами</b>\n\n"
                f"Всего каналов: {len(channels)}\n\n"
                "<i>Выберите канал для управления:</i>"
            )
        
        keyboard = self.keyboard_builder.build_channel_list(channels, page=page)
        
        # Send or edit
        query = update.callback_query
        if query:
            await query.edit_message_text(
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
    
    async def show_content_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show content menu.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info(f"Showing content menu to user {update.effective_user.id}")
        
        # Store navigation
        context.user_data['previous_menu'] = context.user_data.get('current_menu', 'main')
        context.user_data['current_menu'] = 'content'
        
        text = (
            "✍️ <b>Управление контентом</b>\n\n"
            "📝 <b>Сгенерировать</b> - создать новый пост\n"
            "📅 <b>Запланировать</b> - настроить расписание\n"
            "📋 <b>Просмотр постов</b> - посмотреть созданные посты\n\n"
            "<i>Выберите действие:</i>"
        )
        
        keyboard = self.keyboard_builder.build_content_menu()
        
        query = update.callback_query
        if query:
            await query.edit_message_text(
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
    
    async def show_analytics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show analytics menu.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info(f"Showing analytics menu to user {update.effective_user.id}")
        
        # Store navigation
        context.user_data['previous_menu'] = context.user_data.get('current_menu', 'main')
        context.user_data['current_menu'] = 'analytics'
        
        # Delegate to AnalyticsInterface
        if self.bot_controller and self.bot_controller.analytics_interface:
            await self.bot_controller.analytics_interface.show_analytics_menu(update, context)
        else:
            # Fallback if analytics interface not available
            text = (
                "📈 <b>Аналитика</b>\n\n"
                "❌ Интерфейс аналитики недоступен"
            )
            keyboard = self.keyboard_builder.build_back_button("menu:main")
            
            query = update.callback_query
            if query:
                await query.edit_message_text(
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
    
    async def show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show settings menu.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        logger.info(f"Showing settings menu to user {update.effective_user.id}")
        
        # Store navigation
        context.user_data['previous_menu'] = context.user_data.get('current_menu', 'main')
        context.user_data['current_menu'] = 'settings'
        
        # Delegate to SettingsInterface
        if self.bot_controller and self.bot_controller.settings_interface:
            await self.bot_controller.settings_interface.show_settings_menu(update, context)
        else:
            # Fallback if settings interface not available
            text = (
                "⚙️ <b>Настройки</b>\n\n"
                "❌ Интерфейс настроек недоступен"
            )
            keyboard = self.keyboard_builder.build_back_button("menu:main")
            
            query = update.callback_query
            if query:
                await query.edit_message_text(
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
    
    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Go back to previous menu.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        previous_menu = context.user_data.get('previous_menu', 'main')
        logger.info(f"Going back to menu: {previous_menu}")
        
        # Route to appropriate menu
        if previous_menu == 'main':
            await self.show_main_menu(update, context)
        elif previous_menu == 'channels':
            await self.show_channels_menu(update, context)
        elif previous_menu == 'content':
            await self.show_content_menu(update, context)
        elif previous_menu == 'analytics':
            await self.show_analytics_menu(update, context)
        elif previous_menu == 'settings':
            await self.show_settings_menu(update, context)
        else:
            await self.show_main_menu(update, context)
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        current_menu = context.user_data.get('current_menu', 'main')
        
        # Context-specific help
        help_content = {
            'main': (
                "🤖 <b>AI Content Bot</b> - автоматизированное управление каналами\n\n"
                "<b>Основные разделы:</b>\n\n"
                "📊 <b>Каналы</b>\n"
                "Регистрация и управление вашими Telegram каналами. "
                "Здесь вы можете добавлять новые каналы, настраивать их параметры и удалять.\n\n"
                "✍️ <b>Контент</b>\n"
                "Создание и планирование постов. Бот может генерировать контент "
                "с помощью ИИ на заданные темы.\n\n"
                "📈 <b>Аналитика</b>\n"
                "Просмотр статистики по каналам: просмотры, вовлеченность, "
                "топ постов и другие метрики.\n\n"
                "⚙️ <b>Настройки</b>\n"
                "Конфигурация бота: частота публикаций, стиль контента, "
                "уведомления и язык интерфейса.\n\n"
                "⚡ <b>Быстрые действия</b>\n"
                "• <b>Сгенерировать</b> - создать пост с настройками по умолчанию\n"
                "• <b>Статус</b> - посмотреть состояние системы"
            ),
            'channels': (
                "📊 <b>Управление каналами</b>\n\n"
                "<b>Как добавить канал:</b>\n"
                "1. Нажмите <b>Добавить канал</b>\n"
                "2. Отправьте ID канала (например: -1001234567890)\n"
                "3. Укажите название канала\n"
                "4. Канал будет зарегистрирован\n\n"
                "<b>Важно:</b> Бот должен быть администратором канала "
                "с правами на публикацию сообщений.\n\n"
                "<b>Действия с каналом:</b>\n"
                "• <b>Создать пост</b> - сгенерировать контент для канала\n"
                "• <b>Расписание</b> - настроить автоматические публикации\n"
                "• <b>Настроить</b> - изменить параметры канала\n"
                "• <b>Аналитика</b> - посмотреть статистику\n"
                "• <b>Удалить</b> - удалить канал из системы"
            ),
            'content': (
                "✍️ <b>Управление контентом</b>\n\n"
                "<b>Генерация постов:</b>\n"
                "1. Выберите <b>Сгенерировать</b>\n"
                "2. Выберите канал\n"
                "3. Выберите тему или введите свою\n"
                "4. Бот создаст пост с помощью ИИ\n"
                "5. Просмотрите и опубликуйте или отредактируйте\n\n"
                "<b>Планирование:</b>\n"
                "Настройте автоматическую публикацию постов по расписанию. "
                "Бот будет генерировать и публиковать контент в указанное время.\n\n"
                "<b>Просмотр постов:</b>\n"
                "Посмотрите все созданные и опубликованные посты, "
                "их статус и статистику."
            ),
            'analytics': (
                "📈 <b>Аналитика</b>\n\n"
                "<b>Доступные метрики:</b>\n"
                "• 👁️ <b>Просмотры</b> - количество просмотров постов\n"
                "• ❤️ <b>Реакции</b> - лайки и другие реакции\n"
                "• 📤 <b>Репосты</b> - количество пересылок\n"
                "• 💬 <b>Комментарии</b> - активность в комментариях\n"
                "• 📊 <b>Вовлеченность</b> - процент взаимодействий\n\n"
                "<b>Топ постов:</b>\n"
                "Посты с наибольшим количеством просмотров и вовлеченностью.\n\n"
                "<b>Период:</b>\n"
                "Статистика обновляется в реальном времени."
            ),
            'settings': (
                "⚙️ <b>Настройки</b>\n\n"
                "<b>Частота публикаций:</b>\n"
                "Укажите, сколько постов в день должен публиковать бот. "
                "Рекомендуется 2-5 постов в день.\n\n"
                "<b>Стиль контента:</b>\n"
                "• <b>Профессиональный</b> - деловой тон\n"
                "• <b>Casual</b> - неформальный стиль\n"
                "• <b>Юмористический</b> - с шутками и мемами\n\n"
                "<b>Уведомления:</b>\n"
                "Выберите, о каких событиях вы хотите получать уведомления:\n"
                "• Ошибки и проблемы\n"
                "• Завершение публикаций\n"
                "• Важные события\n"
                "• Еженедельная аналитика"
            )
        }
        
        content = help_content.get(current_menu, help_content['main'])
        text = self.formatter.format_help(
            context=current_menu.capitalize(),
            content=content
        )
        
        keyboard = self.keyboard_builder.build_back_button(f"menu:{current_menu}")
        
        query = update.callback_query
        if query:
            await query.edit_message_text(
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
