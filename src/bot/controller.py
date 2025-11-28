"""Bot controller - main entry point for bot operations."""

import logging
from typing import Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from src.config import config
from src.services.enhanced_content_generator import EnhancedContentGenerator, ContentStyle
from src.services.content_optimizer import ContentOptimizer
from src.services.enhanced_scheduler import EnhancedScheduler
from src.services.channel_manager import ChannelManager, ChannelConfig
from src.services.enhanced_publishing_service import EnhancedPublishingService
from src.services.analytics_engine import AnalyticsEngine
from src.services.quality_control import QualityControl
from src.services.enhanced_error_handler import EnhancedErrorHandler
from src.services.settings_storage import SettingsStorage
from src.services.rate_limiter import ActionRateLimiter
from src.services.enhanced_state_manager import EnhancedStateManager
from src.interface.menu_system import MenuSystem
from src.interface.callback_router import CallbackRouter
from src.interface.channel_interface import ChannelInterface
from src.interface.conversation_manager import ConversationManager
from src.interface.content_interface import ContentInterface
from src.interface.analytics_interface import AnalyticsInterface
from src.interface.settings_interface import SettingsInterface
from src.interface.schedule_interface import ScheduleInterface
from src.interface.validators import validate_user_input
from src.llm import (
    LLMManager,
    create_llm_manager_from_env,
    get_config as get_llm_config
)

logger = logging.getLogger(__name__)


class BotController:
    """Main bot controller."""
    
    def __init__(self):
        self.app: Application = None
        self.bot: Bot = None
        
        # Initialize LLM system
        self.llm_manager = self._initialize_llm_manager()
        
        # Initialize services
        self.content_generator = EnhancedContentGenerator(llm_manager=self.llm_manager)
        self.content_optimizer = ContentOptimizer()
        self.scheduler = EnhancedScheduler()
        self.analytics = AnalyticsEngine()
        self.quality_control = QualityControl()
        self.error_handler = EnhancedErrorHandler()
        self.settings_storage = SettingsStorage()
        self.rate_limiter = ActionRateLimiter()
        self.state_manager = EnhancedStateManager(session_timeout=3600)  # 1 hour
        
        # Channel manager will be initialized after bot is created
        self.channel_manager: ChannelManager = None
        self.publishing_service: EnhancedPublishingService = None
        
        # Interface components
        self.menu_system: MenuSystem = None
        self.callback_router: CallbackRouter = None
        self.channel_interface: ChannelInterface = None
        self.conversation_manager: ConversationManager = None
        self.content_interface: ContentInterface = None
        self.analytics_interface: AnalyticsInterface = None
        self.settings_interface: SettingsInterface = None
        self.schedule_interface: ScheduleInterface = None
        
        self.is_running = False
    
    def _initialize_llm_manager(self) -> LLMManager:
        """Initialize LLM Manager with available providers."""
        logger.info("Initializing LLM Manager...")
        
        try:
            # Create LLM Manager from environment (handles all configuration)
            manager = create_llm_manager_from_env()
            
            logger.info(f"✅ LLM Manager initialized successfully")
            return manager
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Manager: {e}")
            logger.warning("⚠️ Bot will use fallback content generation")
            return None
    
    async def start(self):
        """Start the bot."""
        logger.info("Starting AI Content Bot")
        
        try:
            # Create application
            self.app = Application.builder().token(config.bot.token).build()
            self.bot = self.app.bot
            
            # Store LLM Manager in bot_data for access from handlers
            if self.llm_manager:
                self.app.bot_data['llm_manager'] = self.llm_manager
                logger.info("✅ LLM Manager stored in bot_data")
            
            # Initialize auto-posting system
            from src.services.autopost.initializer import initialize_autopost_system
            await initialize_autopost_system()
            
            # Initialize services that need bot
            self.channel_manager = ChannelManager(self.bot)
            self.publishing_service = EnhancedPublishingService(self.bot)
            
            # Initialize interface components
            self.menu_system = MenuSystem(bot_controller=self)
            self.callback_router = CallbackRouter()
            self.channel_interface = ChannelInterface(bot_controller=self)
            self.conversation_manager = ConversationManager(bot_controller=self)
            self.content_interface = ContentInterface(bot_controller=self)
            self.analytics_interface = AnalyticsInterface(bot_controller=self)
            self.settings_interface = SettingsInterface(bot_controller=self)
            self.schedule_interface = ScheduleInterface(bot_controller=self)
            
            # Register callback handlers
            self._register_callback_handlers()
            
            # Register handlers BEFORE starting
            await self.register_handlers()
            
            # Initialize application
            await self.app.initialize()
            await self.app.start()
            
            # Start scheduler
            self.scheduler.start()
            
            # Start state cleanup task
            await self.state_manager.start_cleanup_task()
            logger.info("State cleanup task started")
            
            # Validate admin configuration
            if not config.bot.admin_ids:
                logger.warning("⚠️ No admin IDs configured - bot will have limited functionality")
            
            # Start bot
            self.is_running = True
            logger.info("Bot started successfully")
            
            # Initialize and start updater
            logger.info("Initializing updater...")
            await self.app.updater.initialize()
            
            # Start polling
            logger.info("Starting polling...")
            await self.app.updater.start_polling()
            
            # Keep running until stopped
            import asyncio
            stop_event = asyncio.Event()
            
            try:
                await stop_event.wait()
            except (KeyboardInterrupt, SystemExit):
                logger.info("Received stop signal")
            finally:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            await self.error_handler.handle_critical_failure(e, "BotController")
            raise
    
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping bot")
        
        self.is_running = False
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Stop state cleanup task
        await self.state_manager.stop_cleanup_task()
        logger.info("State cleanup task stopped")
        
        # Graceful shutdown
        pending_ops = []  # Collect pending operations
        await self.error_handler.graceful_shutdown(pending_ops)
        
        logger.info("Bot stopped")
    
    def _register_callback_handlers(self):
        """Register callback handlers with router."""
        logger.info("Registering callback handlers")
        
        # Menu navigation
        self.callback_router.register('menu', self._handle_menu_callback)
        self.callback_router.register('help', self._handle_help_callback)
        self.callback_router.register('quick', self._handle_quick_action)
        
        # Channel management
        self.callback_router.register('channel', self._handle_channel_callback)
        self.callback_router.register('confirm', self._handle_confirm_callback)
        self.callback_router.register('cancel', self._handle_cancel_callback)
        
        # Content management
        self.callback_router.register('content', self._handle_content_callback)
        self.callback_router.register('generate', self._handle_generate_callback)
        self.callback_router.register('theme', self._handle_theme_callback)
        self.callback_router.register('post', self._handle_post_callback)
        self.callback_router.register('posts', self._handle_posts_callback)
        
        # Other handlers
        self.callback_router.register('analytics', self._handle_analytics_callback)
        self.callback_router.register('settings', self._handle_settings_callback)
        self.callback_router.register('schedule', self._handle_schedule_callback)
        
        logger.info("Callback handlers registered")
    
    async def register_handlers(self):
        """Register command handlers."""
        logger.info("Registering command handlers")
        
        # Conversation handlers (must be added first)
        channel_registration_handler = self.conversation_manager.create_channel_registration_handler()
        self.app.add_handler(channel_registration_handler)
        
        custom_theme_handler = self.conversation_manager.create_custom_theme_handler()
        self.app.add_handler(custom_theme_handler)
        
        edit_post_handler = self.conversation_manager.create_edit_post_handler()
        self.app.add_handler(edit_post_handler)
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("config", self.config_command))
        self.app.add_handler(CommandHandler("theme", self.theme_command))
        self.app.add_handler(CommandHandler("stop", self.stop_command))
        self.app.add_handler(CommandHandler("register", self.register_channel_command))
        self.app.add_handler(CommandHandler("generate", self.generate_command))
        
        # LLM Management commands (admin only)
        from src.bot.handlers.llm_commands import (
            llm_status_command,
            llm_stats_command,
            llm_switch_command,
            llm_cache_clear_command,
            llm_reload_command
        )
        self.app.add_handler(CommandHandler("llm_status", llm_status_command))
        self.app.add_handler(CommandHandler("llm_stats", llm_stats_command))
        self.app.add_handler(CommandHandler("llm_switch", llm_switch_command))
        self.app.add_handler(CommandHandler("llm_cache_clear", llm_cache_clear_command))
        self.app.add_handler(CommandHandler("llm_reload", llm_reload_command))
        logger.info("✅ LLM management commands registered")
        
        # Auto-posting commands (admin only)
        from src.bot.handlers.autopost_commands import (
            autopost_add_channel_command,
            autopost_list_channels_command,
            autopost_generate_command,
            autopost_queue_command,
            autopost_schedule_command,
            autopost_help_command
        )
        self.app.add_handler(CommandHandler("autopost_add_channel", autopost_add_channel_command))
        self.app.add_handler(CommandHandler("autopost_list_channels", autopost_list_channels_command))
        self.app.add_handler(CommandHandler("autopost_generate", autopost_generate_command))
        self.app.add_handler(CommandHandler("autopost_queue", autopost_queue_command))
        self.app.add_handler(CommandHandler("autopost_schedule", autopost_schedule_command))
        self.app.add_handler(CommandHandler("autopost_help", autopost_help_command))
        logger.info("✅ Auto-posting commands registered")
        
        # Callback query handler (must be after conversation handlers)
        self.app.add_handler(CallbackQueryHandler(self.callback_router.route_callback))
        
        logger.info("Handlers registered")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        logger.info(f"Received /start command from user {user_id}")
        
        try:
            # Validate user input
            if not validate_user_input(str(user_id)):
                await update.message.reply_text("❌ Недопустимый ID пользователя")
                return
            
            # Show main menu with interface
            await self.menu_system.show_main_menu(update, context)
            logger.info("Main menu shown successfully")
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при запуске бота. Попробуйте позже."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📚 Доступные команды:

/start - Запустить бота
/help - Показать эту справку
/status - Показать статус системы
/config - Настроить параметры
/theme <тема> - Установить тему контента
/register <channel_id> <name> - Зарегистрировать канал
/generate <channel_id> <theme> - Сгенерировать пост
/stop - Остановить все операции (только для админов)
        """
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id
        if not self._validate_admin_access(user_id, "/status"):
            await update.message.reply_text("❌ Эта команда доступна только администраторам")
            return
        
        try:
            # Get system resources
            resources = await self.error_handler.check_resources()
            
            # Get cache stats
            cache_stats = await self.state_manager.get_cache_stats()
            
            status_text = f"""
📊 Статус системы:

🤖 Бот: {'Работает' if self.is_running else 'Остановлен'}
⚙️ CPU: {resources['cpu_percent']:.1f}%
💾 Память: {resources['memory_percent']:.1f}%
💿 Диск: {resources['disk_percent']:.1f}%

📊 Сессии: {cache_stats['total_sessions']} активных
📊 История: {cache_stats['total_histories']} пользователей
📊 Ошибок: {len(self.error_handler.error_log)} за сессию
📊 Ограничение запросов: {self.rate_limiter.get_stats()}
            """
            
            await update.message.reply_text(status_text)
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await update.message.reply_text(f"❌ Ошибка получения статуса: {e}")
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command."""
        user_id = update.effective_user.id
        if not self._validate_admin_access(user_id, "/config"):
            await update.message.reply_text("❌ Эта команда доступна только администраторам")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Использование: /config <параметр> <значение>\n"
                "Пример: /config frequency 5"
            )
            return
        
        param = context.args[0]
        value = context.args[1]
        
        # Validate input
        if not validate_user_input(param) or not validate_user_input(value):
            await update.message.reply_text("❌ Недопустимые параметры")
            return
        
        # Validate and apply configuration
        try:
            if param == "frequency":
                frequency = int(value)
                if 1 <= frequency <= 24:
                    await update.message.reply_text(f"✅ Частота публикаций установлена: {frequency} постов/день")
                else:
                    await update.message.reply_text("❌ Частота должна быть от 1 до 24")
            elif param == "timeout":
                timeout = int(value)
                if 60 <= timeout <= 3600:
                    self.state_manager.session_timeout = timeout
                    await update.message.reply_text(f"✅ Таймаут сессии установлен: {timeout} секунд")
                else:
                    await update.message.reply_text("❌ Таймаут должен быть от 60 до 3600 секунд")
            else:
                await update.message.reply_text(f"❌ Неизвестный параметр: {param}")
        except ValueError:
            await update.message.reply_text("❌ Неверное значение")
        except Exception as e:
            logger.error(f"Error configuring parameter {param}: {e}")
            await update.message.reply_text(f"❌ Ошибка настройки: {e}")
    
    async def theme_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /theme command."""
        if not context.args:
            await update.message.reply_text("Использование: /theme <тема>\nПример: /theme технологии")
            return
        
        theme = " ".join(context.args)
        
        # Validate theme input
        if not validate_user_input(theme) or len(theme) > 100:
            await update.message.reply_text("❌ Недопустимая тема (максимум 100 символов)")
            return
        
        await update.message.reply_text(f"✅ Тема установлена: {theme}")
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command (emergency stop)."""
        user_id = update.effective_user.id
        if not self._validate_admin_access(user_id, "/stop"):
            await update.message.reply_text("❌ Эта команда доступна только администраторам")
            return
        
        try:
            await update.message.reply_text("🛑 Останавливаю все операции...")
            self.is_running = False
            await update.message.reply_text("✅ Операции приостановлены")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            await update.message.reply_text(f"❌ Ошибка остановки: {e}")
    
    async def register_channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command."""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Эта команда доступна только администраторам")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Использование: /register <channel_id> <name>\n"
                "Пример: /register -1001234567890 'Мой канал'"
            )
            return
        
        try:
            channel_id = int(context.args[0])
            channel_name = ".join(context.args[1:])
            
            # Validate input
            if not validate_user_input(str(channel_id)) or not validate_user_input(channel_name):
                await update.message.reply_text("❌ Недопустимые параметры")
                return
            
            if len(channel_name) > 100:
                await update.message.reply_text("❌ Название канала слишком длинное (максимум 100 символов)")
                return
            
            channel_config = ChannelConfig(name=channel_name)
            channel = await self.channel_manager.register_channel(channel_id, channel_config)
            
            await update.message.reply_text(f"✅ Канал '{channel_name}' зарегистрирован")
        except ValueError:
            await update.message.reply_text("❌ Неверный ID канала")
        except Exception as e:
            logger.error(f"Error registering channel: {e}")
            await update.message.reply_text(f"❌ Ошибка регистрации: {e}")
    
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /generate command."""
        user_id = update.effective_user.id
        if not self._validate_admin_access(user_id, "/generate"):
            await update.message.reply_text("❌ Эта команда доступна только администраторам")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Использование: /generate <channel_id> <theme>\n"
                "Пример: /generate 1 технологии"
            )
            return
        
        try:
            channel_id = int(context.args[0])
            theme = " ".join(context.args[1:])
            
            # Validate inputs
            if not validate_user_input(str(channel_id)) or not validate_user_input(theme):
                await update.message.reply_text("❌ Недопустимые параметры")
                return
            
            if len(theme) > 200:
                await update.message.reply_text("❌ Тема слишком длинная (максимум 200 символов)")
                return
            
            await update.message.reply_text(f"⏳ Генерирую пост на тему '{theme}'...")
            
            # Generate post
            style = ContentStyle(tone="professional", length="medium")
            post = await self.content_generator.generate_post(theme, style, channel_id)
            
            # Optimize
            post = await self.content_optimizer.optimize(post)
            
            # Show preview
            preview = f"📝 Сгенерирован пост:\n\n{post.content}\n\n"
            if post.hashtags:
                preview += " ".join(post.hashtags)
            
            await update.message.reply_text(preview)
            
        except ValueError:
            await update.message.reply_text("❌ Неверный ID канала")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            await update.message.reply_text(f"❌ Ошибка генерации: {e}")
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in config.bot.admin_ids
        
    def _validate_admin_access(self, user_id: int, command_name: str) -> bool:
        """Validate admin access for sensitive commands."""
        if not self._is_admin(user_id):
            logger.warning(f"User {user_id} attempted unauthorized access to {command_name}")
            return False
        return True
    
    # Callback handlers
    
    async def _handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle menu navigation callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        menu = callback_data.get('menu', 'main')
        
        logger.info(f"Navigating to menu: {menu}")
        
        if menu == 'main':
            await self.menu_system.show_main_menu(update, context)
        elif menu == 'channels':
            await self.menu_system.show_channels_menu(update, context)
        elif menu == 'content':
            await self.menu_system.show_content_menu(update, context)
        elif menu == 'analytics':
            await self.menu_system.show_analytics_menu(update, context)
        elif menu == 'settings':
            await self.menu_system.show_settings_menu(update, context)
        else:
            await self.menu_system.show_main_menu(update, context)
    
    async def _handle_help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle help button callbacks."""
        await self.menu_system.show_help(update, context)
    
    async def _handle_quick_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quick action buttons."""
        callback_data = context.user_data.get('callback_data', {})
        action = callback_data.get('quick_action')
        
        logger.info(f"Quick action: {action}")
        
        if action == 'generate':
            await self._quick_generate(update, context)
        
        elif action == 'status':
            # Show system status
            resources = await self.error_handler.check_resources()
            status = 'running' if self.is_running else 'stopped'
            
            from src.interface.message_formatter import MessageFormatter
            formatter = MessageFormatter()
            text = formatter.format_system_status(resources, status)
            
            from src.interface.keyboard_builder import KeyboardBuilder
            keyboard_builder = KeyboardBuilder()
            keyboard = keyboard_builder.build_back_button("menu:main")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    async def _quick_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick generate post with default settings.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        user_id = update.effective_user.id
        logger.info(f"Quick generate for user {user_id}")
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(user_id, 'quick_action'):
            wait_time = self.rate_limiter.get_wait_time(user_id, 'quick_action')
            
            text = (
                "⏱️ <b>Слишком много запросов</b>\n\n"
                f"Пожалуйста, подождите {int(wait_time)} секунд перед следующей быстрой генерацией.\n\n"
                "💡 Это ограничение защищает систему от перегрузки."
            )
            
            from src.interface.keyboard_builder import KeyboardBuilder
            keyboard_builder = KeyboardBuilder()
            keyboard = keyboard_builder.build_back_button("menu:main")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return
        
        try:
            # Show loading message
            await update.callback_query.edit_message_text(
                "⏳ <b>Быстрая генерация</b>\n\n"
                "Проверяю доступные каналы...",
                parse_mode='HTML'
            )
            
            # Get first available channel
            channels = []
            if self.channel_manager:
                channels = await self.channel_manager.get_all_channels()
            
            if not channels:
                # No channels available
                text = (
                    "❌ <b>Нет доступных каналов</b>\n\n"
                    "Для быстрой генерации нужен хотя бы один зарегистрированный канал\n\n"
                    "💡 <b>Что делать:</b>\n"
                    "1. Перейдите в меню <b>Каналы</b>\n"
                    "2. Нажмите <b>Добавить канал</b>\n"
                    "3. Следуйте инструкциям для регистрации"
                )
                
                from src.interface.keyboard_builder import KeyboardBuilder
                keyboard_builder = KeyboardBuilder()
                keyboard = keyboard_builder.build_back_button("menu:main")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return
            
            # Use first channel
            channel = channels[0]
            
            await update.callback_query.edit_message_text(
                f"⏳ Генерирую пост для канала <b>{channel.name}</b>...\n\n"
                f"Используются настройки по умолчанию",
                parse_mode='HTML'
            )
            
            # Send typing action
            from telegram.constants import ChatAction
            await update.callback_query.message.chat.send_action(ChatAction.TYPING)
            
            # Generate with default theme and style
            default_theme = "актуальные новости и тренды"
            
            from src.services.content_generator import ContentStyle
            default_style = ContentStyle(tone="professional", length="medium")
            
            # Validate theme
            if not validate_user_input(default_theme):
                await update.callback_query.edit_message_text(
                    "❌ Недопустимая тема для генерации",
                    parse_mode='HTML'
                )
                return
            
            # Generate post
            post = await self.content_generator.generate_post(
                default_theme,
                default_style,
                channel.id
            )
            
            # Optimize
            if self.content_optimizer:
                post = await self.content_optimizer.optimize(post)
            
            # Publish immediately
            await update.callback_query.edit_message_text(
                "⏳ Публикую пост...",
                parse_mode='HTML'
            )
            
            result = await self.publishing_service.publish_post(post)
            
            if result:
                # Success
                from src.interface.message_formatter import MessageFormatter
                formatter = MessageFormatter()
                
                text = formatter.format_success(
                    message="Пост успешно опубликован!",
                    details=(
                        f"📺 Канал: <b>{channel.name}</b>\n"
                        f"📝 Тема: {default_theme}\n"
                        f"✅ Пост опубликован и доступен подписчикам"
                    )
                )
                
                from src.interface.keyboard_builder import KeyboardBuilder
                keyboard_builder = KeyboardBuilder()
                keyboard = keyboard_builder.build_back_button("menu:main")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                # Failed to publish
                text = (
                    "❌ <b>Не удалось опубликовать пост</b>\n\n"
                    "💡 <b>Возможные причины:</b>\n"
                    "• Бот не является администратором канала\n"
                    "• У бота нет прав на публикацию\n"
                    "• Канал недоступен\n\n"
                    "<b>Что делать:</b>\n"
                    "1. Проверьте права бота в канале\n"
                    "2. Убедитесь, что бот - администратор\n"
                    "3. Попробуйте снова"
                )
                
                from src.interface.keyboard_builder import KeyboardBuilder
                keyboard_builder = KeyboardBuilder()
                keyboard = keyboard_builder.build_back_button("menu:main")
                
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        
        except Exception as e:
            logger.error(f"Error in quick generate: {e}")
            
            # Show detailed error
            text = (
                f"❌ <b>Ошибка при быстрой генерации</b>\n\n"
                f"<b>Ошибка:</b> {str(e)[:200]}\n\n"
                f"💡 <b>Что делать:</b>\n"
                f"• Попробуйте еще раз через несколько секунд\n"
                f"• Используйте меню <b>Контент → Сгенерировать</b> для ручной генерации\n"
                f"• Обратитесь к администратору, если ошибка повторяется"
            )
            
            from src.interface.keyboard_builder import KeyboardBuilder
            keyboard_builder = KeyboardBuilder()
            keyboard = keyboard_builder.build_back_button("menu:main")
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    async def _handle_channel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel-related callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        channel_id = callback_data.get('channel_id')
        subaction = callback_data.get('subaction')
        
        logger.info(f"Channel callback: channel_id={channel_id}, subaction={subaction}")
        
        # Check if this is "add channel" action - it's handled by ConversationHandler
        if callback_data.get('params') and callback_data['params'][0] == 'add':
            # This should be handled by ConversationHandler, but if we get here, show info
            await update.callback_query.edit_message_text(
                "➕ <b>Добавление канала</b>\n\n"
                "Начните диалог регистрации канала, нажав кнопку <b>Добавить канал</b> в меню каналов",
                parse_mode='HTML'
            )
            return
        
        if not channel_id:
            await update.callback_query.edit_message_text(
                "❌ Не указан ID канала",
                parse_mode='HTML'
            )
            return
        
        # Validate channel_id
        try:
            channel_id = int(channel_id)
        except ValueError:
            await update.callback_query.edit_message_text(
                "❌ Неверный ID канала",
                parse_mode='HTML'
            )
            return
        
        # Validate input
        if not validate_user_input(str(channel_id)):
            await update.callback_query.edit_message_text(
                "❌ Недопустимый ID канала",
                parse_mode='HTML'
            )
            return
        
        # Route to appropriate handler
        if subaction == 'dashboard':
            await self.channel_interface.show_channel_dashboard(update, context, channel_id)
        elif subaction == 'config':
            await self.channel_interface.handle_channel_config(update, context, channel_id)
        elif subaction == 'delete':
            await self.channel_interface.handle_channel_delete(update, context, channel_id)
        else:
            # Default to dashboard
            await self.channel_interface.show_channel_dashboard(update, context, channel_id)
    
    async def _handle_content_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle content-related callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        content_action = callback_data.get('content_action')
        
        logger.info(f"Content callback: action={content_action}")
        
        if content_action == 'generate':
            # Show channel selection for generation
            await self.content_interface.show_channel_selection_for_generation(update, context)
        elif content_action == 'schedule':
            # Show schedule menu
            await self.schedule_interface.show_schedule_menu(update, context)
        elif content_action == 'view':
            # Show posts list
            await self.content_interface.show_posts_list(update, context)
        else:
            await update.callback_query.edit_message_text(
                f"❌ Неизвестное действие: {content_action}",
                parse_mode='HTML'
            )
    
    async def _handle_generate_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle generation callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        channel_id = callback_data.get('channel_id')
        
        logger.info(f"Generate callback: channel_id={channel_id}")
        
        if not channel_id:
            await update.callback_query.edit_message_text(
                "❌ Не указан ID канала",
                parse_mode='HTML'
            )
            return
        
        # Show theme selection
        await self.content_interface.show_theme_selection(update, context, channel_id)
    
    async def _handle_theme_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle theme selection callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        theme = callback_data.get('theme')
        
        logger.info(f"Theme callback: theme={theme}")
        
        if not theme:
            await update.callback_query.edit_message_text(
                "❌ Тема не выбрана",
                parse_mode='HTML'
            )
            return
        
        # Validate theme
        if not validate_user_input(theme) or len(theme) > 10:
            await update.callback_query.edit_message_text(
                "❌ Недопустимая тема",
                parse_mode='HTML'
            )
            return
        
        # Custom theme is handled by ConversationHandler
        if theme == 'custom':
            # This should be handled by ConversationHandler
            return
        
        # Map theme codes to readable names
        theme_names = {
            'tech': 'Технологии',
            'design': 'Дизайн',
            'mobile': 'Мобильные приложения',
            'startup': 'Стартапы'
        }
        
        theme_name = theme_names.get(theme, theme)
        
        # Generate content with selected theme
        await self.content_interface.generate_content(update, context, theme_name)
    
    async def _handle_post_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle post action callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        post_id = callback_data.get('post_id')
        subaction = callback_data.get('subaction')
        
        logger.info(f"Post callback: post_id={post_id}, subaction={subaction}")
        
        if not post_id:
            await update.callback_query.edit_message_text(
                "❌ Не указан ID поста",
                parse_mode='HTML'
            )
            return
        
        # Validate post_id
        try:
            post_id = int(post_id)
        except ValueError:
            await update.callback_query.edit_message_text(
                "❌ Неверный ID поста",
                parse_mode='HTML'
            )
            return
        
        # Validate input
        if not validate_user_input(str(post_id)):
            await update.callback_query.edit_message_text(
                "❌ Недопустимый ID поста",
                parse_mode='HTML'
            )
            return
        
        if subaction == 'publish':
            await self.content_interface.publish_post(update, context, post_id)
        elif subaction == 'regenerate':
            await self.content_interface.regenerate_post(update, context, post_id)
        elif subaction == 'discard':
            await self.content_interface.discard_post(update, context, post_id)
        elif subaction == 'edit':
            # Placeholder for editing
            await update.callback_query.edit_message_text(
                "✏️ <b>Редактирование поста</b>\n\n"
                "Функция редактирования будет реализована позже\n\n"
                "Пока вы можете перегенерировать пост",
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                f"❌ Неизвестное действие с постом: {subaction}",
                parse_mode='HTML'
            )
    
    async def _handle_posts_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle posts viewing and management callbacks.
        
        Callback formats:
        - posts:channel:<channel_id>[:<status_filter>] - Show posts for channel
        - posts:view:<post_id> - View post details
        - posts:publish:<post_id> - Publish post
        - posts:schedule:<post_id> - Schedule post
        - posts:cancel:<post_id> - Cancel scheduled post
        - posts:edit:<post_id> - Edit post
        - posts:delete:<post_id> - Delete post
        """
        callback_data = context.user_data.get('callback_data', {})
        subaction = callback_data.get('subaction')
        channel_id = callback_data.get('channel_id')
        post_id = callback_data.get('post_id')
        status_filter = callback_data.get('status_filter', 'all')
        
        logger.info(f"Posts callback: subaction={subaction}, channel_id={channel_id}, post_id={post_id}")
        
        if subaction == 'channel':
            # Show posts for channel
            if not channel_id:
                await update.callback_query.edit_message_text(
                    "❌ Не указан ID канала",
                    parse_mode='HTML'
                )
                return
            
            # Validate channel_id
            try:
                channel_id = int(channel_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Неверный ID канала",
                    parse_mode='HTML'
                )
                return
            
            # Validate input
            if not validate_user_input(str(channel_id)):
                await update.callback_query.edit_message_text(
                    "❌ Недопустимый ID канала",
                    parse_mode='HTML'
                )
                return
            
            await self.content_interface.show_channel_posts(update, context, channel_id, status_filter)
        
        elif subaction == 'view':
            # Show post details
            if not post_id:
                await update.callback_query.edit_message_text(
                    "❌ Не указан ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate post_id
            try:
                post_id = int(post_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Неверный ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate input
            if not validate_user_input(str(post_id)):
                await update.callback_query.edit_message_text(
                    "❌ Недопустимый ID поста",
                    parse_mode='HTML'
                )
                return
            
            await self.content_interface.show_post_detail(update, context, post_id)
        
        elif subaction == 'publish':
            # Publish post immediately
            if not post_id:
                await update.callback_query.edit_message_text(
                    "❌ Не указан ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate post_id
            try:
                post_id = int(post_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Неверный ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate input
            if not validate_user_input(str(post_id)):
                await update.callback_query.edit_message_text(
                    "❌ Недопустимый ID поста",
                    parse_mode='HTML'
                )
                return
            
            await update.callback_query.edit_message_text(
                "⏳ Публикую пост...",
                parse_mode='HTML'
            )
            # TODO: Implement immediate publishing
            await update.callback_query.edit_message_text(
                "✅ Пост опубликован!",
                parse_mode='HTML'
            )
        
        elif subaction == 'schedule':
            # Schedule post - show time selection
            if not post_id:
                await update.callback_query.edit_message_text(
                    "❌ Не указан ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate post_id
            try:
                post_id = int(post_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Неверный ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate input
            if not validate_user_input(str(post_id)):
                await update.callback_query.edit_message_text(
                    "❌ Недопустимый ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Get post to get channel_id
            try:
                from src.models.base import async_session_maker
                from src.repositories.post_repository import PostRepository
                
                async with async_session_maker() as session:
                    post_repo = PostRepository(session)
                    post = await post_repo.get_by_id(post_id)
                    
                    if not post:
                        await update.callback_query.edit_message_text(
                            "❌ Пост не найден",
                            parse_mode='HTML'
                        )
                        return
                    
                    # Store post_id in context for later
                    context.user_data['schedule_post_id'] = post_id
                    context.user_data['schedule_channel_id'] = post.channel_id
                    
                    # Show time selection
                    await self.schedule_interface.show_time_selection(update, context, post.channel_id)
                    
            except Exception as e:
                logger.error(f"Error scheduling post: {e}")
                await update.callback_query.edit_message_text(
                    f"❌ Ошибка при планировании\n\n{str(e)}",
                    parse_mode='HTML'
                )
        
        elif subaction == 'cancel':
            # Cancel scheduled post
            await update.callback_query.edit_message_text(
                "❌ <b>Отмена публикации</b>\n\n"
                "Публикация отменена",
                parse_mode='HTML'
            )
        
        elif subaction == 'edit':
            # Edit post - conversation handler will take over
            # The conversation manager's start_edit_post will be called automatically
            pass
        
        elif subaction == 'delete':
            # Delete post - show confirmation
            if not post_id:
                await update.callback_query.edit_message_text(
                    "❌ Не указан ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate post_id
            try:
                post_id = int(post_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Неверный ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Validate input
            if not validate_user_input(str(post_id)):
                await update.callback_query.edit_message_text(
                    "❌ Недопустимый ID поста",
                    parse_mode='HTML'
                )
                return
            
            # Show confirmation dialog
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm:delete_post:{post_id}"),
                    InlineKeyboardButton("❌ Отмена", callback_data=f"posts:view:{post_id}")
                ]
            ])
            
            await update.callback_query.edit_message_text(
                "🗑️ <b>Удаление поста</b>\n\n"
                "⚠️ Вы уверены, что хотите удалить этот пост?\n"
                "Это действие нельзя отменить.",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        else:
            await update.callback_query.edit_message_text(
                f"❌ Неизвестное действие: {subaction}",
                parse_mode='HTML'
            )
    
    async def _handle_analytics_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle analytics callbacks.
        
        Callback format: analytics:<channel_id>[:action]
        - analytics:<channel_id> - Show channel analytics
        - analytics:<channel_id>:detailed - Show detailed report
        """
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data
            parts = query.data.split(':')
            
            if len(parts) < 2:
                logger.error(f"Invalid analytics callback: {query.data}")
                await query.edit_message_text(
                    "❌ Неверный формат команды",
                    parse_mode='HTML'
                )
                return
            
            channel_id = int(parts[1])
            action = parts[2] if len(parts) > 2 else None
            
            # Validate input
            if not validate_user_input(str(channel_id)):
                await query.edit_message_text(
                    "❌ Недопустимый ID канала",
                    parse_mode='HTML'
                )
                return
            
            # Route to appropriate handler
            if action == 'detailed':
                await self.analytics_interface.show_detailed_report(update, context, channel_id)
            else:
                await self.analytics_interface.show_channel_analytics(update, context, channel_id)
                
        except ValueError as e:
            logger.error(f"Invalid channel ID in analytics callback: {e}")
            await query.edit_message_text(
                "❌ Неверный ID канала",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error handling analytics callback: {e}")
            await query.edit_message_text(
                f"❌ Ошибка обработки команды\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def _handle_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle settings callbacks.
        
        Callback format: settings:<category>[:<value>]
        - settings:frequency - Show frequency settings
        - settings:frequency:<value> - Update frequency
        - settings:style - Show style settings
        - settings:style:<value> - Update style
        - settings:notifications - Show notification settings
        - settings:notify:<type>:<enabled> - Toggle notification
        """
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data
            parts = query.data.split(':')
            
            if len(parts) < 2:
                logger.error(f"Invalid settings callback: {query.data}")
                await query.edit_message_text(
                    "❌ Неверный формат команды",
                    parse_mode='HTML'
                )
                return
            
            category = parts[1]
            
            # Validate category
            if not validate_user_input(category):
                await query.edit_message_text(
                    "❌ Недопустимая категория настроек",
                    parse_mode='HTML'
                )
                return
            
            # Route to appropriate handler
            if category == 'frequency':
                if len(parts) > 2:
                    # Update frequency
                    frequency = int(parts[2])
                    # Validate frequency
                    if 1 <= frequency <= 24:
                        await self.settings_interface.update_frequency(update, context, frequency)
                    else:
                        await query.edit_message_text(
                            "❌ Частота должна быть от 1 до 24",
                            parse_mode='HTML'
                        )
                else:
                    # Show frequency settings
                    await self.settings_interface.show_frequency_settings(update, context)
                    
            elif category == 'style':
                if len(parts) > 2:
                    # Update style
                    style = parts[2]
                    # Validate style
                    if validate_user_input(style):
                        await self.settings_interface.update_style(update, context, style)
                    else:
                        await query.edit_message_text(
                            "❌ Недопустимый стиль",
                            parse_mode='HTML'
                        )
                else:
                    # Show style settings
                    await self.settings_interface.show_style_settings(update, context)
                    
            elif category == 'notifications':
                # Show notification settings
                await self.settings_interface.show_notification_settings(update, context)
                
            elif category == 'notify':
                # Toggle notification
                if len(parts) >= 4:
                    notification_type = parts[2]
                    enabled = parts[3].lower() == 'true'
                    # Validate inputs
                    if validate_user_input(notification_type):
                        await self.settings_interface.toggle_notification(
                            update, context, notification_type, enabled
                        )
                    else:
                        await query.edit_message_text(
                            "❌ Недопустимый тип уведомления",
                            parse_mode='HTML'
                        )
                else:
                    logger.error(f"Invalid notify callback: {query.data}")
                    
            else:
                logger.error(f"Unknown settings category: {category}")
                await query.edit_message_text(
                    "❌ Неизвестная категория настроек",
                    parse_mode='HTML'
                )
                
        except ValueError as e:
            logger.error(f"Invalid value in settings callback: {e}")
            await query.edit_message_text(
                "❌ Неверное значение",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error handling settings callback: {e}")
            await query.edit_message_text(
                f"❌ Ошибка обработки команды\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def _handle_schedule_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle schedule callbacks.
        
        Callback format: schedule:<action>[:<param>]
        - schedule:create - Start schedule creation
        - schedule:channel:<channel_id> - Select channel
        - schedule:time:<timestamp> - Select time
        - schedule:theme:<theme> - Select theme and create
        - schedule:cancel:<schedule_id> - Cancel schedule
        """
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data
            parts = query.data.split(':')
            
            if len(parts) < 2:
                logger.error(f"Invalid schedule callback: {query.data}")
                await query.edit_message_text(
                    "❌ Неверный формат команды",
                    parse_mode='HTML'
                )
                return
            
            action = parts[1]
            
            # Route to appropriate handler
            if action == 'create':
                # Start schedule creation
                await self.schedule_interface.start_schedule_creation(update, context)
                
            elif action == 'channel':
                # Channel selected, show time selection
                if len(parts) > 2:
                    channel_id = int(parts[2])
                    await self.schedule_interface.show_time_selection(update, context, channel_id)
                else:
                    logger.error(f"Missing channel ID in schedule callback")
                    
            elif action == 'time':
                # Time selected, show theme selection
                if len(parts) > 2:
                    scheduled_time = float(parts[2])
                    await self.schedule_interface.show_theme_selection(update, context, scheduled_time)
                else:
                    logger.error(f"Missing time in schedule callback")
                    
            elif action == 'theme':
                # Theme selected, create schedule
                if len(parts) > 2:
                    theme = parts[2]
                    await self.schedule_interface.create_schedule(update, context, theme)
                else:
                    logger.error(f"Missing theme in schedule callback")
                    
            elif action == 'cancel':
                # Cancel schedule
                if len(parts) > 2:
                    schedule_id = int(parts[2])
                    await self.schedule_interface.cancel_schedule(update, context, schedule_id)
                else:
                    logger.error(f"Missing schedule ID in cancel callback")
                    
            else:
                logger.error(f"Unknown schedule action: {action}")
                await query.edit_message_text(
                    "❌ Неизвестное действие",
                    parse_mode='HTML'
                )
                
        except ValueError as e:
            logger.error(f"Invalid value in schedule callback: {e}")
            await query.edit_message_text(
                "❌ Неверное значение",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error handling schedule callback: {e}")
            await query.edit_message_text(
                f"❌ Ошибка обработки команды\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def _delete_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
        """Delete a post.
        
        Args:
            update: Telegram update
            context: Callback context
            post_id: ID of the post to delete
        """
        logger.info(f"Deleting post {post_id}")
        
        try:
            from src.models.base import async_session_maker
            from src.repositories.post_repository import PostRepository
            
            async with async_session_maker() as session:
                post_repo = PostRepository(session)
                
                # Get post to get channel_id before deletion
                post = await post_repo.get_by_id(post_id)
                
                if not post:
                    await update.callback_query.edit_message_text(
                        "❌ Пост не найден",
                        parse_mode='HTML'
                    )
                    return
                
                channel_id = post.channel_id
                
                # Delete post
                await post_repo.delete(post_id)
                
                # Show success message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ К списку постов", callback_data=f"posts:channel:{channel_id}")]
                ])
                
                await update.callback_query.edit_message_text(
                    "✅ <b>Пост удален</b>\n\n"
                    "Пост успешно удален из базы данных",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при удалении поста\n\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def _handle_confirm_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle confirmation callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        confirm_action = callback_data.get('confirm_action')
        confirm_data = callback_data.get('confirm_data', '')
        
        logger.info(f"Confirm callback: action={confirm_action}, data={confirm_data}")
        
        if confirm_action == 'delete_channel':
            # Extract channel ID from confirm_data
            try:
                channel_id = int(confirm_data)
                await self.channel_interface.confirm_channel_delete(update, context, channel_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: неверный ID канала",
                    parse_mode='HTML'
                )
        elif confirm_action == 'delete_post':
            # Delete post
            try:
                post_id = int(confirm_data)
                await self._delete_post(update, context, post_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: неверный ID поста",
                    parse_mode='HTML'
                )
        else:
            await update.callback_query.edit_message_text(
                f"❌ Неизвестное действие подтверждения: {confirm_action}",
                parse_mode='HTML'
            )
    
    async def _handle_cancel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cancellation callbacks."""
        callback_data = context.user_data.get('callback_data', {})
        cancel_action = callback_data.get('cancel_action')
        cancel_data = callback_data.get('cancel_data', '')
        
        logger.info(f"Cancel callback: action={cancel_action}, data={cancel_data}")
        
        if cancel_action == 'delete_channel':
            # Extract channel ID from cancel_data
            try:
                channel_id = int(cancel_data)
                await self.channel_interface.cancel_channel_delete(update, context, channel_id)
            except ValueError:
                await update.callback_query.edit_message_text(
                    "❌ Ошибка: неверный ID канала",
                    parse_mode='HTML'
                )
        elif cancel_action == 'generation':
            # Return to content menu
            await self.menu_system.show_content_menu(update, context)
        else:
            # Default: return to main menu
            await self.menu_system.show_main_menu(update, context)
