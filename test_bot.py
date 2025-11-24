#!/usr/bin/env python3
"""
Простой тест бота - проверяет получение обновлений
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from src.config import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_USERNAME = "AniLensBot"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user = update.effective_user
        logger.info(
            f"Received /start from user {user.id} "
            f"(@{user.username or 'no_username'}) "
            f"in chat {update.effective_chat.id}"
        )
        await update.message.reply_text(
            "✅ Bot is working!\n\n"
            "🤖 AI Content Bot\n"
            "Bot is receiving messages correctly."
        )
    except Exception as e:
        logger.error(f"Error in start handler: {e}", exc_info=True)


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command"""
    try:
        user = update.effective_user
        logger.info(f"Received /test from user {user.id}")
        await update.message.reply_text("✅ Test successful!")
    except Exception as e:
        logger.error(f"Error in test handler: {e}", exc_info=True)


def setup_handlers(app: Application) -> None:
    """Register all command handlers"""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    logger.info("Handlers registered")


async def main():
    """Start the bot"""
    logger.info("Starting test bot...")
    
    # Validate configuration
    if not config.bot.token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    logger.info(f"Bot token: {config.bot.token[:20]}...")
    
    # Create application
    app = Application.builder().token(config.bot.token).build()
    
    # Setup handlers
    setup_handlers(app)
    
    try:
        logger.info("Starting polling...")
        
        # Start polling
        await app.initialize()
        await app.start()
        await app.updater.initialize()
        await app.updater.start_polling()
        
        logger.info(f"✅ Bot is running! Send /start or /test to @{BOT_USERNAME}")
        logger.info("Press Ctrl+C to stop")
        
        # Keep running
        stop_event = asyncio.Event()
        await stop_event.wait()
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down...")
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            logger.info("Shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
